import os
import shutil
import subprocess
import argparse
from pyfiglet import Figlet
from rich.progress import Progress
from rich.console import Console
from rich import print

console = Console()

class DiskImageHandler:
    def __init__(self, image_path, mount_point):
        self.image_path = image_path
        self.mount_point = mount_point

    def create_disk_image(self, size_in_mb):
        size_in_bytes = size_in_mb * 1024 * 1024
        with open(self.image_path, 'wb') as img_file:
            img_file.truncate(size_in_bytes)
        console.log(f"[green]Disk image created at {self.image_path} with size {size_in_mb} MB[/green]")

    def format_disk_image(self):
        console.log("[yellow]Formatting disk image...[/yellow]")
        subprocess.run(['mkfs.ext4', self.image_path], check=True)
        console.log(f"[green]Disk image {self.image_path} formatted as ext4 filesystem[/green]")

    def mount_disk_image(self):
        os.makedirs(self.mount_point, exist_ok=True)
        console.log(f"[yellow]Mounting disk image {self.image_path} at {self.mount_point}...[/yellow]")
        subprocess.run(['sudo', 'mount', '-o', 'loop', self.image_path, self.mount_point], check=True)
        console.log(f"[green]Disk image mounted at {self.mount_point}[/green]")

    def unmount_disk_image(self):
        console.log(f"[yellow]Unmounting disk image from {self.mount_point}...[/yellow]")
        subprocess.run(['sudo', 'umount', self.mount_point], check=True)
        console.log(f"[green]Disk image unmounted from {self.mount_point}[/green]")


class FolderHandler:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_folder_size(self):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def copy_folder_to_disk(self, destination):
        console.log(f"[yellow]Copying contents from {self.folder_path} to {destination}...[/yellow]")
        with Progress() as progress:
            task = progress.add_task("[green]Copying files...", total=len(os.listdir(self.folder_path)))
            shutil.copytree(self.folder_path, destination, dirs_exist_ok=True)
            progress.update(task, advance=1)
        console.log(f"[green]Copied contents of {self.folder_path} to {destination}[/green]")

    def extract_folder_from_disk(self, destination):
        os.makedirs(destination, exist_ok=True)
        console.log(f"[yellow]Extracting contents from {self.folder_path} to {destination}...[/yellow]")
        with Progress() as progress:
            task = progress.add_task("[green]Extracting files...", total=len(os.listdir(self.folder_path)))
            shutil.copytree(self.folder_path, destination, dirs_exist_ok=True)
            progress.update(task, advance=1)
        console.log(f"[green]Extracted contents to {destination}[/green]")


class BackupHandler:
    def __init__(self, root_folder, image_path, mount_point):
        self.root_folder = root_folder
        self.disk_handler = DiskImageHandler(image_path, mount_point)
        self.folder_handler = FolderHandler(root_folder)

    def backup_to_virtual_disk(self):
        console.log(f"[yellow]Calculating the size of {self.root_folder}...[/yellow]")
        total_size_bytes = self.folder_handler.get_folder_size()
        total_size_mb = (total_size_bytes // (1024 * 1024)) + 50  # Add some extra space for file system overhead
        console.log(f"[green]Total folder size is {total_size_mb} MB[/green]")

        self.disk_handler.create_disk_image(total_size_mb)
        self.disk_handler.format_disk_image()
        self.disk_handler.mount_disk_image()
        self.folder_handler.copy_folder_to_disk(self.disk_handler.mount_point)
        self.disk_handler.unmount_disk_image()

        console.log(f"[green]Backup completed to virtual disk {self.disk_handler.image_path}[/green]")

    def extract_from_virtual_disk(self, destination_folder):
        self.disk_handler.mount_disk_image()
        folder_handler = FolderHandler(self.disk_handler.mount_point)
        folder_handler.extract_folder_from_disk(destination_folder)
        self.disk_handler.unmount_disk_image()

        console.log(f"[green]Extraction completed from {self.disk_handler.image_path} to {destination_folder}[/green]")


def main():
    f = Figlet(font='slant')
    print(f.renderText('VaultGen'))
    parser = argparse.ArgumentParser(description="Backup and extract folder contents using a virtual disk image.")
    parser.add_argument("operation", choices=["backup", "extract"], help="Choose whether to backup or extract.")
    parser.add_argument("--folder", help="The folder to backup or the destination to extract to.")
    parser.add_argument("--image", help="The disk image file path.")
    parser.add_argument("--mount", default="/mnt/virtual_disk", help="The mount point for the disk image.")
    
    args = parser.parse_args()

    if args.operation == "backup":
        if not args.folder or not args.image:
            console.log("[red]You must specify both --folder (source) and --image (output) for backup.[/red]")
            return
        backup_handler = BackupHandler(args.folder, args.image, args.mount)
        backup_handler.backup_to_virtual_disk()
    
    elif args.operation == "extract":
        if not args.folder or not args.image:
            console.log("[red]You must specify both --folder (destination) and --image (input) for extraction.[/red]")
            return
        backup_handler = BackupHandler(None, args.image, args.mount)
        backup_handler.extract_from_virtual_disk(args.folder)


if __name__ == "__main__":
    main()
