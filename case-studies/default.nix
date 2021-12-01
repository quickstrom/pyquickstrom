{ pkgs ? (import ../nix/nixpkgs.nix), quickstrom ? import ../default.nix { } }:
let
  todomvc = import ./todomvc.nix;
  src = pkgs.nix-gitignore.gitignoreSource [ ] ./.;

  case-studies-packages = python-pkgs: with python-pkgs; [ click ];
  python = pkgs.python38.withPackages case-studies-packages;

  deps = [
    pkgs.chromedriver
    pkgs.chromium
    pkgs.geckodriver
    pkgs.firefox
    quickstrom
  ];

  run-case-studies = pkgs.writeShellScriptBin "run-case-studies" ''
    mkdir -p /tmp/case-studies
    cd /tmp/case-studies

    for i in ${pkgs.lib.concatStringsSep " " deps}; do
        export PATH="$i/bin:$PATH"
    done

    DISPLAY=:99 TODOMVC_DIR=${todomvc} ${python}/bin/python ${src}/run.py
  '';

  imageWithUser = user: let
    nonRootShadowSetup = { user, uid, gid ? uid }:
      with pkgs; [
        (writeTextDir "etc/shadow" ''
          root:!x:::::::
          ${user}:!:::::::
        '')
        (writeTextDir "etc/passwd" ''
          root:x:0:0::/root:${runtimeShell}
          ${user}:x:${toString uid}:${toString gid}::/home/${user}:
        '')
        (writeTextDir "etc/group" ''
          root:x:0:
          ${user}:x:${toString gid}:
        '')
        (writeTextDir "etc/gshadow" ''
          root:x::
          ${user}:x::
        '')
      ];
  in pkgs.dockerTools.buildImage {
    name = "with-user";
    tag = "latest";
    contents = nonRootShadowSetup user;
  };

  docker-image = pkgs.dockerTools.buildImage {
    name = "case-studies";
    fromImage = imageWithUser {
      uid = 1000;
      user = "app";
    };
    contents = [pkgs.bash pkgs.coreutils run-case-studies];
    extraCommands = "mkdir -m 0777 tmp";

    config = {
      User = "app";
      Cmd = [ "run-case-studies" ];
    };
  };
in { inherit run-case-studies docker-image; }
