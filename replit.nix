{ pkgs }: {
  deps = [
    pkgs.build2
    pkgs.sqlite-interactive.bin
    pkgs.inetutils
  ];
}