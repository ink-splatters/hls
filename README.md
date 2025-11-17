# HLS

Tool for manipulating HLS (m3u8) playlists.

## TODO

- [x] m3u8 network source
- [x] dumping segment urls
- [ ] downloading (and / or delegating DL to download manager)
- [ ] concatenating segments (`cat <segments...> | ffmpeg -i - -c copy out.mp4)`)
- [ ] streaming server ( different segment size, optional media processing)
