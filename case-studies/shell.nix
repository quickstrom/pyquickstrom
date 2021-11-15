{ pkgs ? (import ../nix/nixpkgs.nix), quickstrom ? import ../default.nix { } }:
let
  todomvc = builtins.fetchTarball {
    url =
      "https://github.com/tastejs/todomvc/archive/41ba86db92336c11e56d425c5151b7ec2932be9a.tar.gz";
  };
in pkgs.mkShell {
  buildInputs = [ pkgs.chromedriver pkgs.geckodriver quickstrom pkgs.python38 ]
    ++ pkgs.lib.optional pkgs.stdenv.isLinux [ pkgs.firefox pkgs.chromium ];
  TODOMVC_DIR = todomvc;
}
