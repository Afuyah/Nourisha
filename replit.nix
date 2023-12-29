{ pkgs }: {
  deps = [
    pkgs.sqlite-interactive.bin
    pkgs.inetutils
  ];
}