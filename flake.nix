{
  description = "Description for the project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
    flake-root.url = "github:srid/flake-root";
    # agenix-shell.url = "github:aciceri/agenix-shell";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
        inputs.flake-root.flakeModule
        # inputs.agenix-shell.flakeModules.default
      ];
      systems = [ "x86_64-linux" "i686-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      
      # agenix-shell = {
      #   secrets = {
      #     ouath1_token.file = /home/ibecker/code/github/streak-tracker/secrets/ouath1_token.age;
      #     ouath2_token.file = /home/ibecker/code/github/streak-tracker/secrets/ouath2_token.age;
      #   };
      #   identityPaths = [ "/home/ibecker/code/github/streak-tracker/key.txt" ];
      #   # secretsPath = "/home/ibecker/code/github/streak-tracker/secrets";
      # };

      perSystem = { config, self', inputs', pkgs, system, lib, ... }: {
        # Per-system attributes can be defined here. The self' and inputs'
        # module parameters provide easy access to attributes of the same
        # system.


        # Equivalent to  inputs'.nixpkgs.legacyPackages.hello;
        packages.default = pkgs.git;


        devenv.shells.default = {
          name = "streak-tracker";

          dotenv = {
            enable = true;
            filename = ".env.local";
          };
          
          languages.python = {
            enable = true;
            poetry.enable = true;
          };



          imports = [
            # This is just like the imports in devenv.nix.
            # See https://devenv.sh/guides/using-with-flake-parts/#import-a-devenv-module
            # ./devenv-foo.nix
          ];

          # https://devenv.sh/reference/options/
          packages = [ 
            config.packages.default
            pkgs.python3Packages.pip
            pkgs.just
            # pkgs.rage
          ];

          # enterShell = ''
          #   source ${lib.getExe config.agenix-shell.installationScript}
          # '';
        };

      };
      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
