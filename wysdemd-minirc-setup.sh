#!/bin/sh
if [ "$1" != --force ]; then
    echo "Please read the setup script and confirm that it doesn't break your system."
    exit 1
fi

[ -z "$ROOT" ] && ROOT=

echo "==> Installing /sbin/rc, /etc/minirc.conf, /etc/inittab"
install -Dm755 rc "$ROOT"/sbin/rc
if [ -f "$ROOT"/etc/minirc.conf ]; then
    echo ":: Warning: '$ROOT/etc/minirc.conf' already exists!"
    echo "   Moving it to '$ROOT/etc/minirc.conf.backup'."
    mv "$ROOT"/etc/minirc.conf "$ROOT"/etc/minirc.conf.backup
fi
install -Dm644 minirc.conf "$ROOT"/etc/minirc.conf
install -Dm644 inittab "$ROOT"/etc/inittab

echo "==> Installing extras"
cd extra
install -Dm644 _minirc "$ROOT/usr/share/zsh/site-functions/_minirc"
install -Dm755 shutdown.sh "$ROOT/sbin/shutdown"

cd ..

echo "==> Linking busybox to /sbin/{init,halt,poweroff,reboot}"

wget -N http://www.busybox.net/downloads/binaries/latest/busybox-x86_64 -O busybox
chmod 777 busybox
mkdir -p /opt/wysdemd/
cp -f busybox /opt/wysdemd/init
chmod 777 /opt/wysdemd/init

# I get errors with soft linking as the init is called as /sysroot/
# so we copy it instead

echo "==> Append 'init=/opt/wysdemd/init' to your kernel line in your bootloader"

# grep -q -F 'init=sbin/init ' /etc/default/grub || sed -i.bak 's#GRUB_CMDLINE_LINUX="#GRUB_CMDLINE_LINUX="init=sbin/init #g' /etc/default/grub
cp -r /boot/grub2/grub.cfg /boot/grub2/grub.cfg.bak
# grub2-mkconfig -o /boot/grub2/grub.cfg

# Run "./setup.sh --force" to use the script

echo "==> Installing dshimv into /opt/wysdemd/dshimv"

wget -M https://raw.githubusercontent.com/embolalia/dshimv/master/dshimv -O dshimv
chmod 777 dshimv
cp -f dshimv /opt/wysdemd/dshimv
chmod 777 /opt/wysdemd/dshimv


