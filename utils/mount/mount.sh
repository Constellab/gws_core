#!/bin/bash

disk="sdb"
part="${disk}1"

if [ "`lsblk | grep $disk`" ]; then
    # sdb partition is found
    
    if [ "`cat /proc/mounts | grep $disk`" == "" ]; then
        
        # sdb is not mounted
        
        if [ "`lsblk | grep $part`" == "" ]; then
            # create the partion
            echo "Create partition $part"
            
            (
            echo o # Create a new empty DOS partition table
            echo n # Add a new partition
            echo p # Primary partition
            echo 1 # Partition number
            echo   # First sector (Accept default: 1)
            echo   # Last sector (Accept default: varies)
            echo w # Write changes
            ) | sudo fdisk /dev/${disk}

            # format partition
            sudo mkfs.ext4 -F /dev/${part}
        fi
        
        # mount partition
        echo "Mount disk $disk"
        sudo mkdir -p /mnt/store
        sudo mount /dev/${part} /mnt/store
        
    else:
        echo "Disk $disk already mounted"
    fi
fi