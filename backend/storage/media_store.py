"""
Media storage module using GridFS.

Handles all media file operations including:
- Upload images and videos
- Retrieve files
- Delete files
- File metadata management
"""

from typing import Any, Dict, List, Optional, BinaryIO
from bson import ObjectId
from gridfs import GridFS, GridFSBucket, NoFile
from pymongo import MongoClient
from pymongo.database import Database

from .connection import get_db, MongoDBConnection


class MediaStore:
    """
    Storage operations for media files using GridFS.
    """
    
    def __init__(self, bucket_name: str = "media"):
        """
        Initialize the media store.
        
        Args:
            bucket_name: GridFS bucket name
        """
        self.bucket_name = bucket_name
        self._bucket: Optional[GridFSBucket] = None
    
    @property
    def bucket(self) -> GridFSBucket:
        """
        Get the GridFS bucket.
        
        Returns:
            GridFSBucket instance
        """
        if self._bucket is None:
            db = get_db()
            if db is None:
                raise RuntimeError("Database not connected")
            self._bucket = GridFSBucket(db, bucket_name=self.bucket_name)
        return self._bucket
    
    @property
    def fs_collection(self):
        """
        Get the GridFS files collection.
        
        Returns:
            Collection instance for fs.files
        """
        db = get_db()
        if db is None:
            raise RuntimeError("Database not connected")
        return db[f"{self.bucket_name}.files"]
    
    def save_file(self, file_data: bytes, filename: str,
                  content_type: str,
                  metadata: Optional[Dict[str, Any]] = None) -> ObjectId:
        """
        Save a file to GridFS.
        
        Args:
            file_data: File content as bytes
            filename: Filename to store
            content_type: MIME type (e.g., 'image/jpeg', 'video/mp4')
            metadata: Optional metadata dict
            
        Returns:
            ObjectId of the saved file
        """
        upload_options = {
            'metadata': {'contentType': content_type}
        }

        if metadata:
            upload_options['metadata'].update(metadata)

        return self.bucket.upload_from_stream(
            filename,
            file_data,
            **upload_options
        )
    
    def save_file_from_path(self, file_path: str,
                            content_type: str,
                            metadata: Optional[Dict[str, Any]] = None) -> ObjectId:
        """
        Save a file from a file path.
        
        Args:
            file_path: Path to the file
            content_type: MIME type
            metadata: Optional metadata dict
            
        Returns:
            ObjectId of the saved file
        """
        filename = file_path.split('/')[-1]
        upload_options = {
            'metadata': {'contentType': content_type}
        }

        if metadata:
            upload_options['metadata'].update(metadata)

        with open(file_path, 'rb') as f:
            return self.bucket.upload_from_stream(
                filename,
                f.read(),
                **upload_options
            )
    
    def get_file(self, file_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by ID.
        
        Args:
            file_id: File's ObjectId
            
        Returns:
            File metadata dict or None
        """
        return self.fs_collection.find_one({'_id': file_id})
    
    def get_file_data(self, file_id: ObjectId) -> Optional[bytes]:
        """
        Get file content by ID.
        
        Args:
            file_id: File's ObjectId
            
        Returns:
            File content as bytes or None
        """
        try:
            stream = self.bucket.open_download_stream(file_id)
            return stream.read()
        except NoFile:
            return None
    
    def get_file_stream(self, file_id: ObjectId):
        """
        Get file stream by ID for efficient streaming.
        
        Args:
            file_id: File's ObjectId
            
        Returns:
            GridOut stream or None
        """
        try:
            return self.bucket.open_download_stream(file_id)
        except NoFile:
            return None
    
    def delete_file(self, file_id: ObjectId) -> bool:
        """
        Delete a file from GridFS.
        
        Args:
            file_id: File's ObjectId
            
        Returns:
            True if deleted successfully
        """
        try:
            self.bucket.delete(file_id)
            return True
        except NoFile:
            return False
    
    def get_files_by_user(self, user_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all files uploaded by a user.
        
        Args:
            user_id: User's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of file metadata
        """
        return list(self.fs_collection.find(
            {'metadata.user_id': user_id}
        ).limit(limit))
    
    def get_files_by_post(self, post_id: ObjectId,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all files associated with a post.
        
        Args:
            post_id: Post's ObjectId
            limit: Maximum number of results
            
        Returns:
            List of file metadata
        """
        return list(self.fs_collection.find(
            {'metadata.post_id': post_id}
        ).limit(limit))
    
    def get_files_by_type(self, media_type: str,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get files by media type.
        
        Args:
            media_type: "image" or "video"
            limit: Maximum number of results
            
        Returns:
            List of file metadata
        """
        return list(self.fs_collection.find(
            {'metadata.media_type': media_type}
        ).limit(limit))
    
    def update_file_metadata(self, file_id: ObjectId,
                             metadata: Dict[str, Any]) -> bool:
        """
        Update file metadata.
        
        Args:
            file_id: File's ObjectId
            metadata: New metadata dict
            
        Returns:
            True if updated successfully
        """
        result = self.fs_collection.update_one(
            {'_id': file_id},
            {'$set': {'metadata': metadata}}
        )
        return result.modified_count > 0
    
    def get_file_size(self, file_id: ObjectId) -> Optional[int]:
        """
        Get file size in bytes.
        
        Args:
            file_id: File's ObjectId
            
        Returns:
            File size or None
        """
        file_doc = self.get_file(file_id)
        return file_doc.get('length') if file_doc else None
    
    def get_total_size_by_user(self, user_id: ObjectId) -> int:
        """
        Get total storage used by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Total bytes used
        """
        files = self.get_files_by_user(user_id)
        return sum(f.get('length', 0) for f in files)
    
    def delete_files_by_user(self, user_id: ObjectId) -> int:
        """
        Delete all files uploaded by a user.
        
        Args:
            user_id: User's ObjectId
            
        Returns:
            Number of files deleted
        """
        files = self.get_files_by_user(user_id)
        count = 0
        for file_doc in files:
            if self.delete_file(file_doc['_id']):
                count += 1
        return count
    
    def delete_files_by_post(self, post_id: ObjectId) -> int:
        """
        Delete all files associated with a post.
        
        Args:
            post_id: Post's ObjectId
            
        Returns:
            Number of files deleted
        """
        files = self.get_files_by_post(post_id)
        count = 0
        for file_doc in files:
            if self.delete_file(file_doc['_id']):
                count += 1
        return count
