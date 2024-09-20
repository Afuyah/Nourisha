{ pkgs }: {
  deps = [
    pkgs.dig
    pkgs.build2
    pkgs.sqlite-interactive.bin
    pkgs.inetutils
  ];
}