let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.jupyter
      python-pkgs.pandas
      python-pkgs.pillow
      python-pkgs.matplotlib
      python-pkgs.torchWithoutCuda
      python-pkgs.torchvision#-bin
      python-pkgs.captum
      python-pkgs.flask-compress
      python-pkgs.huggingface-hub
      python-pkgs.datasets
      python-pkgs.pyarrow
    ]))
  ];
}
