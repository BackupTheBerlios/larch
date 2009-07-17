#TODO
# Modified bits of rc.sysinit - how to include them?

f_header ()
{
    echo " "
    printhl "Live CD based on Arch Linux"
    printsep
}

f_fscheck ()
{
    stat_busy "Initializing /etc/mtab"
    #/bin/mount -n -o remount,rw /

    /bin/rm -f /etc/mtab*

    # Make entries for aufs/unionfs, tmpfs and live medium in /etc/mtab
    grep "^aufs */ " /proc/mounts >>/etc/mtab
    grep "^unionfs */ " /proc/mounts >>/etc/mtab
    grep "^tmpfs */.livesys " /proc/mounts >>/etc/mtab
    if [ -d /.livesys/medium/larch ]; then
        grep " /.livesys/medium " /proc/mounts >>/etc/mtab
    fi

    stat_done

}

