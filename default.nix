{ pkgs ? (import ./nix/nixpkgs.nix), specstrom ? import ./nix/specstrom.nix
, includeBrowsers ? true }:
let
  poetry2nix = import ./nix/poetry2nix.nix { inherit pkgs; };

  quickstrom = poetry2nix.mkPoetryApplication {
    projectDir = ./.;
    python = pkgs.python39;
    propagatedBuildInputs = [ specstrom ];
    checkInputs = [ pkgs.nodePackages.pyright ];
    checkPhase = ''
      pyright -p . quickstrom tests
      pytest
    '';

  };

  client-side = import ./client-side { inherit pkgs; };
  html-report = import ./html-report { inherit pkgs; };

  runtimeDeps = [ specstrom pkgs.chromedriver ]
    ++ pkgs.lib.optionals includeBrowsers [ pkgs.chromium ];

  quickstrom-wrapped = { includeBrowsers }:
    pkgs.symlinkJoin {
      name = "quickstrom";
      paths = [ quickstrom ];
      buildInputs = [ pkgs.makeWrapper ];
      postBuild = ''
        mkdir -p $out/share
        cp -r ${./ulib} $out/share/ulib
        wrapProgram $out/bin/quickstrom \
          --set QUICKSTROM_CLIENT_SIDE_DIRECTORY ${client-side} \
          --set QUICKSTROM_HTML_REPORT_DIRECTORY ${html-report} \
          --set PATH ${pkgs.lib.makeBinPath runtimeDeps} \
          --add-flags "-I$out/share/ulib"

      '';
    };

  docker = pkgs.dockerTools.buildImage {
    name = "quickstrom";
    contents =
      [ pkgs.coreutils (quickstrom-wrapped { includeBrowsers = true; }) ];
    config = { Cmd = [ "quickstrom" ]; };
  };
in {
  quickstrom = quickstrom-wrapped { inherit includeBrowsers; };
  docker = docker;
}

