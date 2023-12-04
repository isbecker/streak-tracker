![Run Streak](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fisbecker%2Fstreak-tracker%2Fmain%2Fstreak.json&query=%24.total_count&label=Run%20Streak&color=lawngreen)

# Garmin Connect Streak Tracker

This is a simple script that allows you to login to Garmin Connect and track your current run streak.

## Installation

First, you should install nix. Not strictly necessary, but it makes things easier.
Otherwise, you will need to install the dependencies manually.

## Components

- nix
  - [direnv](https://github.com/direnv/direnv)
  - [devenv](https://devenv.sh)
- [just](https://github.com/casey/just)
  - run `just -l` to see what tasks are supported
- python

## Usage

### Nix-based development environment

This one liner will install the dependencies and drop you into a shell with them available.

```console
nix develop --impure
```

From there, you can run `just -l` to see what tasks are supported.

### Login

In order to use this script, you need to login to Garmin Connect and save the session tokens. This project uses [cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect/) (which uses [matin/garth](https://github.com/matin/garth) for auth). You will be prompted for your email and password.

Assuming you are already in the nix development environment, you can run the following command to login.

```console
just login
```

Once you have the login tokens, you can save them in `.env.local`. The `.envrc` file will automatically load this file, if it exists. See `.env` for the required variables.

If you are not in the devenv shell, you can run this one-liner to login. This is how the GitHub Action works (although that doesn't use the login command; see below).

```console
nix develop --impure --command just login
```

### Track a run

If you have done a run today, you can run the following command to update your streak.

```console
just ran
```

And if you aren't in the devenv shell:

```console
nix develop --impure --command just ran
```
