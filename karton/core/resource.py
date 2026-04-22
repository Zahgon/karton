import contextlib
import hashlib
import os
import shutil
import tempfile
import uuid
import zipfile
from io import BytesIO
from typing import IO, TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union, cast
if TYPE_CHECKING:
    from .backend import KartonBackend

class ResourceBase(object):
    """
    Base resource class, contains the basic logic of both remote and
    local resources. If you're not implementing your own resource metatypes
    you'll probably want to look at `:py:meth:`LocalResource or
    `:py:meth:` RemoteResource instead.

    :param name: Name of the resource (e.g. name of file)
    :param content: Resource content
    :param path: Path of file with resource content
    :param bucket: Alternative S3 bucket for resource
    :param metadata: Resource metadata
    :param sha256: Resource sha256 hash
    :param _uid: Alternative S3 resource id
    :param _flags: Resource flags
    """
    DIRECTORY_FLAG = 'Directory'

    def __init__(self, name: str, content: Optional[Union[str, bytes]]=None, path: Optional[str]=None, bucket: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, sha256: Optional[str]=None, fd: Optional[IO[bytes]]=None, _uid: Optional[str]=None, _size: Optional[int]=None, _flags: Optional[List[str]]=None) -> None:
        self.name = name
        self.bucket = bucket
        self.metadata = metadata or {}
        sha256 = sha256 or self.metadata.get('sha256')
        calculate_hash = sha256 is None
        self._content: Optional[bytes] = None
        if content and path:
            raise ValueError("Can't set both path and content for resource")
        if path:
            if not os.path.isfile(path):
                raise IOError("Path {path} doesn't exist or is not a file".format(path=path))
            if calculate_hash:
                sha256_hash = hashlib.sha256()
                with open(path, 'rb') as f:
                    for byte_block in iter(lambda: f.read(4096), b''):
                        sha256_hash.update(byte_block)
                sha256 = sha256_hash.hexdigest()
        elif fd is not None:
            if calculate_hash:
                sha256_hash = hashlib.sha256()
                last_position = fd.tell()
                fd.seek(0)
                for byte_block in iter(lambda: fd.read(4096), b''):
                    sha256_hash.update(byte_block)
                sha256 = sha256_hash.hexdigest()
                fd.seek(last_position)
        elif content:
            if isinstance(content, str):
                self._content = content.encode()
            elif isinstance(content, bytes):
                self._content = content
            else:
                raise TypeError('Content can be bytes or str only')
            if calculate_hash and self._content:
                sha256 = hashlib.sha256(self._content).hexdigest()
        self.metadata['sha256'] = sha256
        self._uid = _uid or str(uuid.uuid4())
        self._path = path
        self._size = _size
        self._flags = _flags or []

    @property
    def uid(self) -> str:
        """
        Resource identifier (UUID)

        :return: Resource identifier
        """
        pass

    @property
    def content(self) -> bytes:
        """
        Resource content. Must be overriden in a derived class.

        :return: Resource contents
        """
        raise NotImplementedError()

    @property
    def size(self) -> int:
        """
        Resource size

        :return: Resource size
        """
        pass

    @property
    def sha256(self) -> Optional[str]:
        """
        Resource sha256

        :return: Hexencoded resource SHA256 hash
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        pass

class LocalResourceBase(ResourceBase):

    def __init__(self, name: str, content: Optional[Union[str, bytes]]=None, path: Optional[str]=None, bucket: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, uid: Optional[str]=None, sha256: Optional[str]=None, fd: Optional[IO[bytes]]=None, _flags: Optional[List[str]]=None, _close_fd: bool=False) -> None:
        if len(list(filter(None, [path, content, fd]))) != 1:
            raise ValueError('You must exclusively provide a path, content or fd')
        super().__init__(name, content=content, path=path, bucket=bucket, metadata=metadata, sha256=sha256, fd=fd, _uid=uid, _flags=_flags)
        self.fd = fd
        self._close_fd = _close_fd

    @property
    def content(self) -> bytes:
        """
        Resource content. Reads the file if the file was not read before.

        :return: Content bytes
        """
        pass

    @property
    def size(self) -> int:
        """
        Resource size

        :return: Resource size
        """
        pass

    @classmethod
    def from_directory(cls, name: str, directory_path: str, compression: int=zipfile.ZIP_DEFLATED, in_memory: bool=False, bucket: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, uid: Optional[str]=None) -> 'LocalResourceBase':
        """
        Resource extension, allowing to pass whole directory as a zipped resource.

        Reads all files contained in directory_path recursively and packs them
        into zip file.

        .. code-block:: python

            # Creating zipped resource from path
            dumps = LocalResource.from_directory("dumps", directory_path="dumps/")

        :param name: Name of the resource (e.g. name of file)
        :param directory_path: Path of the resource directory
        :param compression: Compression level (default is zipfile.ZIP_DEFLATED)
        :param in_memory: Don't create temporary file and make in-memory zip file                           (default: False)
        :param bucket: Alternative S3 bucket for resource
        :param metadata: Resource metadata
        :param uid: Alternative S3 resource id
        :return: :class:`LocalResource` instance with zipped contents
        """
        pass

class LocalResource(LocalResourceBase):
    """
    Represents local resource with arbitrary binary data e.g. file contents.

    Local resources will be uploaded to object hub (S3) during
    task dispatching.

    .. code-block:: python

        # Creating resource from bytes
        sample = Resource("original_name.exe", content=b"X5O!P%@AP[4\\
        PZX54(P^)7CC)7}$EICAR-STANDARD-ANT...")

        # Creating resource from path
        sample = Resource("original_name.exe", path="sample/original_name.exe")

    :param name: Name of the resource (e.g. name of file)
    :param content: Resource content
    :param path: Path of file with resource content
    :param bucket: Alternative S3 bucket for resource
    :param metadata: Resource metadata
    :param uid: Alternative S3 resource id
    :param sha256: Resource sha256 hash
    :param fd: Seekable file descriptor
    :param _flags: Resource flags
    :param _close_fd: Close file descriptor after upload (default: False)
    """

    def _upload(self, backend: 'KartonBackend') -> None:
        """Internal function for uploading resources

        :param backend: KartonBackend to use while uploading the resource

        :meta private:
        """
        pass

    def upload(self, backend: 'KartonBackend') -> None:
        """Internal function for uploading resources

        :param backend: KartonBackend to use while uploading the resource

        :meta private:
        """
        pass
Resource = LocalResource

class RemoteResource(ResourceBase):
    """
    Keeps reference to remote resource object shared between subsystems
    via object storage (S3)

    Should never be instantiated directly by subsystem, but can be directly passed to
    outgoing payload.

    :param name: Name of the resource (e.g. name of file)
    :param bucket: Alternative S3 bucket for resource
    :param metadata: Resource metadata
    :param uid: Alternative S3 resource id
    :param size: Resource size
    :param backend: :py:meth:`KartonBackend` to bind to this resource
    :param sha256: Resource sha256 hash
    :param _flags: Resource flags
    """

    def __init__(self, name: str, bucket: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, uid: Optional[str]=None, size: Optional[int]=None, backend: Optional['KartonBackend']=None, sha256: Optional[str]=None, _flags: Optional[List[str]]=None) -> None:
        super(RemoteResource, self).__init__(name, bucket=bucket, metadata=metadata, sha256=sha256, _uid=uid, _size=size, _flags=_flags)
        self.backend = backend

    def loaded(self) -> bool:
        """
        Checks whether resource is loaded into memory

        :return: Flag indicating if the resource is loaded or not
        """
        pass

    @classmethod
    def from_dict(cls, dict: Dict[str, Any], backend: Optional['KartonBackend']) -> 'RemoteResource':
        """
        Internal deserialization method for remote resources

        :param dict: Serialized information about resource
        :param backend: KartonBackend object
        :return: Deserialized :py:meth:`RemoteResource` object

        :meta private:
        """
        pass

    @property
    def content(self) -> bytes:
        """
        Resource content. Performs download when resource was not loaded before.

        :return: Content bytes
        """
        pass

    def unload(self) -> None:
        """
        Unloads resource object from memory
        """
        pass

    def remove(self) -> None:
        """
        Internal remote resource remove method

        :meta private:
        """
        pass

    def download(self) -> bytes:
        """
        Downloads remote resource content from object hub into memory.

        .. code-block:: python

            sample = self.current_task.get_resource("sample")

            # Ensure that resource will be downloaded before it will be
            # passed to processing method
            sample.download()

            self.process_sample(sample)

        :return: Downloaded content bytes
        """
        pass

    def download_to_file(self, path: str) -> None:
        """
        Downloads remote resource into file.

        .. code-block:: python

            sample = self.current_task.get_resource("sample")

            sample.download_to_file("sample/sample.exe")

            with open("sample/sample.exe", "rb") as f:
                contents = f.read()

        :param path: Path to download the resource into
        """
        pass

    @contextlib.contextmanager
    def download_temporary_file(self, suffix=None) -> Iterator[IO[bytes]]:
        """
        Downloads remote resource into named temporary file.

        .. code-block:: python

            sample = self.current_task.get_resource("sample")

            with sample.download_temporary_file() as f:
                contents = f.read()
                path = f.name

            # Temporary file is deleted after exitting the "with" scope

        :return: ContextManager with the temporary file
        """
        pass

    @contextlib.contextmanager
    def zip_file(self) -> Iterator[zipfile.ZipFile]:
        """
        If resource contains a Zip file, downloads it to the temporary file
        and wraps it with ZipFile object.

        .. code-block:: python

            dumps = self.current_task.get_resource("dumps")

            with dumps.zip_file() as zipf:
                print("Fetched dumps: ", zipf.namelist())

        By default: method downloads zip into temporary file, which is deleted after
        leaving the context. If you want to load zip into memory,
        call :py:meth:`RemoteResource.download` first.

        If you want to pre-download Zip under specified path and open it using
        zipfile module, you need to do this manually:

        .. code-block:: python

            dumps = self.current_task.get_resource("dumps")

            # Download zip file
            zip_path = "./dumps.zip"
            dumps.download_to_file(zip_path)

            zipf = zipfile.Zipfile(zip_path)

        :return: ContextManager with zipfile
        """
        pass

    def extract_to_directory(self, path: str) -> None:
        """
        If resource contains a Zip file, extracts files contained in Zip into
        provided path.

        By default: method downloads zip into temporary file, which is deleted
        after extraction. If you want to load zip into memory, call
        :py:meth:`RemoteResource.download` first.

        :param path: Directory path where the resource should be unpacked
        """
        pass

    @contextlib.contextmanager
    def extract_temporary(self) -> Iterator[str]:
        """
        If resource contains a Zip file, extracts files contained in Zip
        to the temporary directory.

        Returns path of directory with extracted files. Directory is recursively
        deleted after leaving the context.

        .. code-block:: python

            dumps = self.current_task.get_resource("dumps")

            with dumps.extract_temporary() as dumps_path:
                print("Fetched dumps:", os.listdir(dumps_path))

        By default: method downloads zip into temporary file, which is deleted
        after extraction. If you want to load zip into memory, call
        :py:meth:`RemoteResource.download` first.

        :return: ContextManager with the temporary directory
        """
        pass
