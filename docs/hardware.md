# Hardware

The machine is a spare AMD64 PC. The processor is an Intel Core i7-3770. The GPU is an Asus Dual Radeon RX 580 4 GB (Polaris, Ellesmere). The TV plugs into that card.

The card takes one 8-pin PCIe power plug. The socket is on the top edge of the card, at the end opposite the video ports, tucked into the cooler shroud. Join the PSU's 6-pin and its 2-pin latch into one plug. The spare PC's Thermaltake 630 W supply has that cable.

`lspci -nn` names this chip Ellesmere and lists the whole RX 470/480/570/580/590 family on one line, with device id `1002:67df`. Some RX 580 boards report `1002:6fdf`. The installer accepts either id.

## OS

Install Kubuntu 26.04 LTS amd64. Kubuntu 26.10 is also accepted. Leave the kernel on the distro's current version. Kubuntu 26.04 ships Plasma 6.6 and kernel 7.0, and the in-tree `amdgpu` module drives this card.

The login session is Plasma (X11), from the `plasma-session-x11` package, session name `plasmax11`. Kubuntu 26.04 boots Plasma on Wayland unless that session is selected. The launcher raises windows with `wmctrl` and reads the focused window with `xdotool`, which need the X11 session. The Flirc is an ordinary keyboard on either session.

## Display stack

- Kernel driver: `amdgpu`.
- Userspace: `mesa-libgallium` (VA-API and OpenGL) and `vainfo`.
- Vulkan, when the archive still ships it: `mesa-vulkan-drivers`.
- Firmware: `linux-firmware` (the Polaris blobs).

The installer checks `lspci` before it changes the login session. After the packages are in place it runs `vainfo` and looks for `VAProfileHEVCMain10` with `VAEntrypointVLD`. A reboot loads the firmware if that entry is missing on the first check.

```bash
vainfo --display drm
```

HDMI audio is the RX 580's own HDMI device. The i7-3770's motherboard HDMI is a second sink and is not the one the TV uses. `skip-htpc audio` selects an HDMI PulseAudio or PipeWire sink, preferring the one on PCI bus `01` (the x16 slot on this board). Set `audio_sink` in `config.json` when the card enumerates somewhere else.

## What the GPU can decode

In Kodi, set the render method to VAAPI and turn on HEVC VAAPI. Hardware decode covers H.264, MPEG-2, VC-1, VP9, and HEVC, including 10-bit HEVC. AV1 is software. HDMI 2.0 on this card carries 4K60. Keep AV1 out of the library.

Chrome is started with one `--enable-features` line, `AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL`, and `--use-gl=desktop`. `LIBVA_DRIVER_NAME` is `radeonsi`. `chrome://gpu` should list hardware video decode after a title starts. Linux Widevine is L3, so Netflix stays around 720p. The RX 580 does not raise that limit. YouTube TV can use the VP9 decoder.
