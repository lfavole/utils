# My personal GRUB theme

This theme is mostly optimized for 1600x900 displays.

To install, run:
```sh
sudo cp -r grub-theme-lfavole/ /boot/grub/themes/lfavole/
sudo sed -i.bak '/^GRUB_THEME=/c\GRUB_THEME="/boot/grub/themes/lfavole/theme.txt"' /etc/default/grub
```

[Theme and icons source](https://linuxiac.com/how-to-apply-theme-to-grub-boot-loader/)

[Background source](https://github.com/vinceliuice/grub2-themes/blob/a9dab5c/backgrounds/1080p/background-tela.jpg)
