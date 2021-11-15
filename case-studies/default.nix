{ pkgs ? (import ../nix/nixpkgs.nix), specstrom ? null
, quickstrom ? import ../default.nix { inherit specstrom; } }:
let
  src = pkgs.nix-gitignore.gitignoreSource [ ] ./.;

  deps = [ pkgs.chromedriver pkgs.geckodriver quickstrom pkgs.python38 ]
    ++ pkgs.lib.optional pkgs.stdenv.isLinux [ pkgs.firefox pkgs.chromium ];

  run = pkgs.writeShellScriptBin "run-case-studies" ''
    for i in ${pkgs.lib.concatStringsSep " " deps}; do
        export PATH="$i/bin:$PATH"
    done
    pushd ${src}
    python run.py
    popd ${src}
  '';
in pkgs.dockerTools.buildImage {
  name = "case-studies";
  config = { Cmd = [ "${run}/bin/run-case-studies" ]; };
}
