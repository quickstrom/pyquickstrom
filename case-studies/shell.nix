{ pkgs ? (import ../nix/nixpkgs.nix), specstrom ? import ../nix/specstrom.nix, quickstrom ? import ../default.nix { inherit specstrom; } }:
let
  todomvc = import ./todomvc.nix;
in pkgs.mkShell {
  buildInputs = [ pkgs.chromedriver pkgs.geckodriver quickstrom pkgs.python38 ]
    ++ pkgs.lib.optional pkgs.stdenv.isLinux [ pkgs.firefox pkgs.chromium ];
  TODOMVC_DIR = todomvc;
}
