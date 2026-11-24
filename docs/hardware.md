# Hardware

The machine is a spare AMD64 PC. The GPU is a GeForce GTX 1050 Ti (GP107, Pascal, 4 GB).

Pascal's last NVIDIA branch is 580. That series is still updated for new Linux kernels. Drivers after 580, including 590 and newer, do not support this card. The open kernel modules do not support it either. `ubuntu-drivers install` on a current Ubuntu will offer a newer branch, and the display will not start on this GPU.

## OS

Use Ubuntu 24.04 LTS. Ubuntu 26.04 is also accepted. Both can install the proprietary 580 driver, and the kernel does not need to be held.

- Install `nvidia-driver-580`, the proprietary metapackage. Do not install `nvidia-driver-580-open` or `nvidia-open`.
- The Team Kodi PPA was retired in 2024, so the installer uses the distro `kodi` package. Flatpak Kodi is not the default: the launcher looks for the native window class `Kodi`.
- The installer asks apt what `nvidia-driver-580` depends on. It installs the package only when the version is 580.x and the dependencies stay on the 580 proprietary packages. If the candidate is a transitional wrapper that pulls another branch, it pins that release's `-updates` pocket out of the way once and checks again. If that still is not a real 580 driver, it leaves the display driver untouched.

Ubuntu's packaged 580 modules are signed. If the reboot comes back to a black screen, the module did not load. From a text console, `nvidia-smi` should report a 580.x driver. Enroll the DKMS module's MOK, or turn Secure Boot off, and reboot again.

## Nouveau

Nouveau drives the desktop without the proprietary module. Kodi then decodes on the CPU. That is the fallback if 580 will not install:

```bash
sudo apt purge 'nvidia*'
sudo apt install xserver-xorg-video-nouveau
sudo reboot
```

## What the GPU can decode

In Kodi, with the 580 driver, set the render method to VDPAU (or Automatic). Hardware decode covers H.264, MPEG-2, VC-1, and HEVC, including 10-bit HEVC. The GPU also decodes VP9. Kodi's VDPAU path may still play VP9 in software. AV1 is software. HDMI 2.0 on this card carries 4K60. Keep AV1 out of the library.

Chrome on this driver should be left on its normal compositor path. Forcing VAAPI on the NVIDIA driver often produces a black video surface. 720p Netflix in software is the expected web path, because Linux Widevine is L3. The 1050 Ti does not raise that limit.

HDMI audio is the GTX 1050 Ti's own HDMI device. `skip-htpc audio` selects the first PulseAudio or PipeWire sink whose name contains `hdmi`.
