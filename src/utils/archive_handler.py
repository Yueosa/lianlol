"""压缩包处理工具"""
import base64
import io
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import py7zr
from PIL import Image


# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
# 支持的压缩包格式
ARCHIVE_EXTENSIONS = {'.zip', '.7z'}
# 最大解压大小（防止压缩炸弹）- 500MB
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024

# 危险文件扩展名（可能包含恶意代码）
DANGEROUS_EXTENSIONS = {
    # 可执行文件
    '.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif',
    '.app', '.dmg', '.pkg',  # macOS
    '.sh', '.bin', '.run',   # Linux
    # 脚本文件
    '.js', '.vbs', '.vbe', '.jse', '.ws', '.wsf', '.wsc', '.wsh',
    '.ps1', '.psm1', '.psd1',  # PowerShell
    '.py', '.pyw', '.pyc', '.pyo',  # Python
    '.rb', '.pl', '.php',  # 其他脚本
    # Office 宏
    '.docm', '.xlsm', '.pptm', '.dotm', '.xltm', '.potm',
    # 其他危险文件
    '.jar', '.class',  # Java
    '.dll', '.sys', '.drv',  # Windows 系统文件
    '.lnk', '.url',  # 快捷方式
    '.reg',  # 注册表
    '.hta', '.html', '.htm',  # 可能包含脚本的网页
    '.svg',  # 可能包含 JavaScript
}


class ArchiveHandler:
    """压缩包处理器"""
    
    def __init__(self, archive_path: Path):
        """初始化处理器
        
        Args:
            archive_path: 压缩包文件路径
        """
        self.archive_path = archive_path
        self.archive_type = self._get_archive_type()
        
    def _get_archive_type(self) -> str:
        """获取压缩包类型"""
        ext = self.archive_path.suffix.lower()
        if ext == '.zip':
            return 'zip'
        elif ext == '.7z':
            return '7z'
        else:
            raise ValueError(f"不支持的压缩包格式: {ext}")
    
    def list_files(self) -> List[str]:
        """列出压缩包中的所有文件
        
        Returns:
            文件路径列表
        """
        try:
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    return zf.namelist()
            else:  # 7z
                with py7zr.SevenZipFile(self.archive_path, 'r') as szf:
                    return szf.getnames()
        except Exception as e:
            raise ValueError(f"无法读取压缩包: {str(e)}")
    
    def list_images(self) -> List[str]:
        """列出压缩包中的所有图片文件
        
        Returns:
            图片文件路径列表
        """
        all_files = self.list_files()
        images = []
        
        for file_path in all_files:
            # 跳过目录
            if file_path.endswith('/'):
                continue
            
            # 检查扩展名
            ext = Path(file_path).suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                images.append(file_path)
        
        return images
    
    def extract_file(self, file_path: str, output_dir: Path) -> Path:
        """从压缩包中提取单个文件
        
        Args:
            file_path: 压缩包内的文件路径
            output_dir: 输出目录
            
        Returns:
            提取后的文件路径
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理文件名，避免路径遍历攻击
        safe_filename = Path(file_path).name
        output_path = output_dir / safe_filename
        
        try:
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    # 读取文件内容
                    data = zf.read(file_path)
                    # 写入到输出路径
                    output_path.write_bytes(data)
            else:  # 7z
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    with py7zr.SevenZipFile(self.archive_path, 'r') as szf:
                        # 7z需要先提取到临时目录
                        szf.extract(temp_path, targets=[file_path])
                        # 找到提取的文件并移动
                        extracted = temp_path / file_path
                        if extracted.exists():
                            shutil.copy2(extracted, output_path)
                        else:
                            raise FileNotFoundError(f"文件提取失败: {file_path}")
        except Exception as e:
            raise ValueError(f"提取文件失败: {str(e)}")
        
        return output_path
    
    def get_metadata(self) -> Dict:
        """获取压缩包元数据
        
        Returns:
            元数据字典
        """
        all_files = self.list_files()
        images = self.list_images()
        
        return {
            "filename": self.archive_path.name,
            "size": self.archive_path.stat().st_size,
            "total_files": len(all_files),
            "image_count": len(images)
        }
    
    def get_image_thumbnail(self, file_path: str, max_size: int = 200) -> Optional[str]:
        """从压缩包中提取图片并生成 Base64 缩略图
        
        Args:
            file_path: 压缩包内的图片路径
            max_size: 缩略图最大尺寸
            
        Returns:
            Base64 编码的缩略图数据 (data URI 格式)，失败返回 None
        """
        try:
            # 提取图片数据
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    data = zf.read(file_path)
            else:  # 7z
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    with py7zr.SevenZipFile(self.archive_path, 'r') as szf:
                        szf.extract(temp_path, targets=[file_path])
                        extracted = temp_path / file_path
                        if extracted.exists():
                            data = extracted.read_bytes()
                        else:
                            return None
            
            # 生成缩略图
            img = Image.open(io.BytesIO(data))
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # 转换为 JPEG 格式的 Base64
            buffer = io.BytesIO()
            # 处理透明图片
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=85)
            b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/jpeg;base64,{b64_data}"
            
        except Exception as e:
            print(f"生成缩略图失败 {file_path}: {str(e)}")
            return None
    
    def get_thumbnails(self, image_list: List[str], max_count: int = 50) -> List[Dict]:
        """批量生成图片缩略图
        
        Args:
            image_list: 图片路径列表
            max_count: 最大处理数量
            
        Returns:
            包含路径和缩略图的字典列表
        """
        result = []
        for img_path in image_list[:max_count]:
            thumbnail = self.get_image_thumbnail(img_path)
            result.append({
                "path": img_path,
                "name": Path(img_path).name,
                "thumbnail": thumbnail
            })
        return result
    
    def get_full_image(self, file_path: str, max_size: int = 800) -> Optional[str]:
        """从压缩包中提取图片并生成较大的 Base64 预览图
        
        Args:
            file_path: 压缩包内的图片路径
            max_size: 预览图最大尺寸
            
        Returns:
            Base64 编码的图片数据 (data URI 格式)，失败返回 None
        """
        try:
            # 提取图片数据
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    data = zf.read(file_path)
            else:  # 7z
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    with py7zr.SevenZipFile(self.archive_path, 'r') as szf:
                        szf.extract(temp_path, targets=[file_path])
                        extracted = temp_path / file_path
                        if extracted.exists():
                            data = extracted.read_bytes()
                        else:
                            return None
            
            # 生成较大的预览图
            img = Image.open(io.BytesIO(data))
            # 只有当图片超过 max_size 时才缩放
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # 转换为 JPEG 格式的 Base64
            buffer = io.BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=90)
            b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/jpeg;base64,{b64_data}"
            
        except Exception as e:
            print(f"生成预览图失败 {file_path}: {str(e)}")
            return None


def smart_select_preview_images(
    image_list: List[str],
    count: int = 3
) -> List[str]:
    """智能选择预览图片
    
    优先选择带编号的图片（如 01.jpg, 02.jpg），否则随机选择
    
    Args:
        image_list: 图片文件列表
        count: 需要选择的图片数量
        
    Returns:
        选中的图片文件列表
    """
    if not image_list:
        return []
    
    if len(image_list) <= count:
        return image_list
    
    # 尝试找出带数字编号的图片
    numbered_images = []
    pattern = re.compile(r'(\d+)')
    
    for img_path in image_list:
        filename = Path(img_path).stem
        matches = pattern.findall(filename)
        if matches:
            # 提取第一个数字作为排序依据
            try:
                number = int(matches[0])
                numbered_images.append((number, img_path))
            except ValueError:
                pass
    
    # 如果找到带编号的图片，按编号排序并取前N个
    if numbered_images:
        numbered_images.sort(key=lambda x: x[0])
        return [img for _, img in numbered_images[:count]]
    
    # 否则，按文件名排序取前N个（字母序）
    sorted_images = sorted(image_list)
    return sorted_images[:count]


def extract_preview_images(
    archive_path: Path,
    preview_dir: Path,
    selected_images: Optional[List[str]] = None,
    auto_select_count: int = 3
) -> Tuple[List[str], Dict]:
    """提取预览图片
    
    Args:
        archive_path: 压缩包路径
        preview_dir: 预览图片输出目录
        selected_images: 手动指定的图片列表（压缩包内路径）
        auto_select_count: 自动选择时的图片数量
        
    Returns:
        (预览图片相对URL列表, 压缩包元数据)
    """
    handler = ArchiveHandler(archive_path)
    
    # 获取元数据
    metadata = handler.get_metadata()
    
    # 确定要提取的图片
    if selected_images:
        # 使用手动指定的图片
        images_to_extract = selected_images
    else:
        # 自动选择
        all_images = handler.list_images()
        images_to_extract = smart_select_preview_images(all_images, auto_select_count)
    
    # 创建预览目录
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    # 提取图片
    preview_urls = []
    for idx, img_path in enumerate(images_to_extract):
        try:
            # 提取文件
            extracted_path = handler.extract_file(img_path, preview_dir)
            
            # 验证是否为有效图片
            try:
                with Image.open(extracted_path) as img:
                    img.verify()
            except Exception:
                # 不是有效图片，跳过
                extracted_path.unlink(missing_ok=True)
                continue
            
            # 重命名为统一格式
            new_filename = f"preview_{idx + 1}{extracted_path.suffix}"
            new_path = preview_dir / new_filename
            extracted_path.rename(new_path)
            
            # 生成相对URL（假设 preview_dir 在 static/uploads/ 下）
            # 例如: /static/uploads/2026-01/previews/123/preview_1.jpg
            relative_parts = new_path.parts
            static_idx = relative_parts.index('static')
            url = '/' + '/'.join(relative_parts[static_idx:])
            preview_urls.append(url)
            
        except Exception as e:
            print(f"提取预览图失败 {img_path}: {str(e)}")
            continue
    
    # 更新元数据中的预览图列表
    metadata['preview_images'] = preview_urls
    
    return preview_urls, metadata


def validate_archive(archive_path: Path) -> Tuple[bool, str]:
    """验证压缩包文件
    
    Args:
        archive_path: 压缩包路径
        
    Returns:
        (是否有效, 错误信息)
    """
    # 检查文件扩展名
    ext = archive_path.suffix.lower()
    if ext not in ARCHIVE_EXTENSIONS:
        return False, f"不支持的压缩包格式: {ext}"
    
    try:
        handler = ArchiveHandler(archive_path)
        
        # 尝试列出文件
        files = handler.list_files()
        
        # 检查文件数量（防止过多文件）
        if len(files) > 10000:
            return False, "压缩包文件数量过多（超过10000个）"
        
        # 检查是否包含危险文件
        dangerous_files = []
        for file_path in files:
            if file_path.endswith('/'):
                continue  # 跳过目录
            file_ext = Path(file_path).suffix.lower()
            if file_ext in DANGEROUS_EXTENSIONS:
                dangerous_files.append(Path(file_path).name)
        
        if dangerous_files:
            # 最多显示5个危险文件名
            shown_files = dangerous_files[:5]
            more = f"等 {len(dangerous_files)} 个" if len(dangerous_files) > 5 else ""
            return False, f"压缩包包含可能有危险的文件类型: {', '.join(shown_files)}{more}"
        
        # 估算解压后大小（简单检查）
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                total_size = sum(info.file_size for info in zf.infolist())
                if total_size > MAX_EXTRACTED_SIZE:
                    return False, f"解压后大小超过限制（{MAX_EXTRACTED_SIZE / 1024 / 1024:.0f}MB）"
        
        return True, ""
        
    except Exception as e:
        return False, f"压缩包验证失败: {str(e)}"


def is_archive_file(filename: str) -> bool:
    """检查是否为压缩包文件
    
    Args:
        filename: 文件名
        
    Returns:
        是否为压缩包
    """
    ext = Path(filename).suffix.lower()
    return ext in ARCHIVE_EXTENSIONS
