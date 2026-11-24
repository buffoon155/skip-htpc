# Hardware

The machine is a spare AMD64 PC. The GPU is a GeForce GTX 660 (GK106, Kepler).

Kepler's last NVIDIA branch is 470. The last NVIDIA release on that branch is 470.256.02 (June 2024). Drivers 495 and newer, including 535, 550, and 580, do not support this card. `ubuntu-drivers install` on a current Ubuntu will offer one of those and the display will not start.

## OS

Use Ubuntu 22.04 LTS.

- Kernel 5.15 or 6.8 can build the 470 module. Kernel 6.14 and newer need out-of-tree patches this installer does not apply, so the installer refuses `--nvidia` there.
- Ubuntu 22.04's `kodi` package is 19.4. The Team Kodi PPA was retired in 2024, so the installer uses the distro package. Flatpak Kodi is not the default: the Flatpak NVIDIA runtime rarely matches a 470 driver, and the launcher looks for the native window class `Kodi`.
- As of November 2026, Ubuntu has retired the 470 branch and has also discussed shipping it again as an unsigned DKMS module. `jammy-updates` has at times replaced `nvidia-driver-470` with a wrapper that installs 535. The installer asks apt what the candidate depends on. It installs the package only when the version is 470.x and the dependencies stay on the 470 packages. If the candidate is the wrapper, it pins that release's `-updates` pocket out of the way once and checks again. If that still is not a real 470 driver, it leaves the display driver untouched.

Secure Boot must be off, or the DKMS module's MOK must be enrolled. An unsigned 470 module will not load while Secure Boot is on, and the reboot comes back to a black screen.

## Nouveau

Nouveau drives the desktop without the proprietary module. Kodi then decodes H.264 on the CPU. That is the fallback if 470 will not install:

```bash
sudo apt purge 'nvidia*'
sudo apt install xserver-xorg-video-nouveau
sudo reboot
```

## What the GPU can decode

In Kodi, with the 470 driver, set the render method to VDPAU (or Automatic). Hardware decode covers H.264, MPEG-2, and VC-1. HEVC, VP9, and AV1 are software, and a 660 is a poor software decoder for those. Keep the library in H.264 at 1080p or lower when you can.

Chrome on this driver should be left on its normal compositor path. Forcing VAAPI on the 470 driver often produces a black video surface. 720p Netflix in software is the expected web path.

HDMI audio is the GTX 660's own HDMI device. `skip-htpc audio` selects the first PulseAudio or PipeWire sink whose name contains `hdmi`.
