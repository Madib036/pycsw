name: CodSpeed Benchmarks

on:
  push:
    branches:
      - "main" # or "master"
  pull_request:
  # `workflow_dispatch` allows CodSpeed to trigger backtest
  # performance analysis in order to generate initial data.
  workflow_dispatch:

jobs:
  benchmarks:
    name: Run benchmarks
    runs-on: ubuntu-latest
    permissions: # optional for public repositories
      contents: read # required for actions/checkout
      id-token: write # required for OIDC authentication with CodSpeed
    steps:
      - uses: actions/checkout@v5
      # ...
      # Setup your environment here:
      #  - Configure your Python/Rust/Node version
      #  - Install your dependencies
      #  - Build your benchmarks (if using a compiled language)
      # ...
      - name: Run the benchmarks
        uses: CodSpeedHQ/action@v4
        with:
          mode: simulation
          run: <Insert your benchmark command here>