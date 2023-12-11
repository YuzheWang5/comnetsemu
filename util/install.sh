#!/usr/bin/env bash
#
# About: All-in-one ComNetsEmu installer script
#
# The installation of ComNetsEmu is managed by the Ansible with playbooks located in ./playbooks/
# This script is just a tiny wrapper to run Ansible playbooks on localhost for local installation
# and keep the CLI interface of the old ComNetsEmu versions (before 0.3.0)
#

set -x

# Fail on error
set -e

# Fail on unset var usage
set -o nounset

# Avoid conflicts with custom grep options
unset GREP_OPTIONS

# Use en_US locale
unset LANG
unset LANGUAGE
LC_ALL=en_US.utf8
export LC_ALL

######################
#  Helper Functions  #
######################

function print_stderr() {
    printf '%b\n' "$1" >&2
}

function warning() {
    declare _type=$1 text=$2
    print_stderr "\033[33mWarning:\033[0m ${_type} ${text}"
}

function error() {
    declare _type=$1 text=$2
    print_stderr "\033[31m[✘]\033[0m ${_type} ${text}"
}

####################
#  Sanity Checks   #
####################

# Mininet's installer's default assumption.
if [[ $EUID -eq 0 ]]; then
    error "[USER]" "Do not run this script through sudo or as root user."
    echo "This installer script should be run as a regular user with sudo permissions, "
    echo "not root (Avoid running all commands in the script with root privilege) !"
    echo "The script will call sudo when needed."
    echo "Please use bash ./install.sh instead of sudo bash ./install.sh"
    exit 1
fi

ARCH=$(uname -m)
if [[ "$ARCH" == "i686" ]]; then
    error "[ARCH]" "i386 is not supported. Please use X86_64."
    exit 1
fi

# ComNetsEmu is fully tested under the LTS version
UBUNTU_RELEASE_1="20.04"
# Additional supported version with warning
UBUNTU_RELEASE_2="22.04"
# Truly non-interactive apt-get installation
INSTALL="sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q install"
UPDATE="sudo apt-get update --fix-missing"

DIST=Unknown
grep Ubuntu /etc/lsb-release &>/dev/null && DIST="Ubuntu"
if [ "$DIST" = "Ubuntu" ]; then
    if ! lsb_release -v &>/dev/null; then
        $INSTALL lsb-release
    fi
    CURRENT_VERSION=$(lsb_release -rs)
    if [[ $CURRENT_VERSION != "$UBUNTU_RELEASE_1" && $CURRENT_VERSION != "$UBUNTU_RELEASE_2" ]]; then
        error "[DIST]" "This installer ONLY supports Ubuntu $UBUNTU_RELEASE_1 LTS and Ubuntu $UBUNTU_RELEASE_2 LTS."
        exit 1
    fi

    if [[ $CURRENT_VERSION = "$UBUNTU_RELEASE_2" ]]; then
        echo "Warning: You are using Ubuntu $UBUNTU_RELEASE_2 LTS, which has not been fully tested with this installer."
    fi
else
    error "[DIST]" "This installer ONLY supports Ubuntu $UBUNTU_RELEASE_1 LTS and Ubuntu $UBUNTU_RELEASE_2 LTS."
    exit 1
fi

# Check if required tools are already available in PATH.
NEEDED_CMDS=(
    ansible
    git
    pip3
    python3
    sed
    sudo
)

# Function to install a command
install_cmd() {
    echo "Attempting to install $1..."
    sudo apt-get install -qq $1 >/dev/null 2>&1
}

for cmd in "${NEEDED_CMDS[@]}"; do
    if ! command -v "$cmd" >/dev/null; then
        echo "$cmd is not installed. Trying to install..."
        install_cmd "$cmd"
        if ! command -v "$cmd" >/dev/null; then
            echo "Failed to install $cmd. Please install it manually."
            exit 1
        fi
    fi
done

echo "All necessary commands are installed."

####################
#  Main Installer  #
####################

echo "*** ComNetsEmu Installer ***"

function usage() {
    printf '\nUsage: %s [-ahu]\n\n' "$(basename "$0")" >&2
    # Less options, less problems...
    echo "Options:"
    echo " -a: Install ComNetsEmu and (A)ll its dependencies. Good luck with your Internet connection!"
    echo " -h: Print usage/(H)elp."
    echo " -u: (U)pgrade installed ComNetsEmu and all its dependencies."
    exit 2
}

function ansible_install_comnetsemu_localhost() {
    SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
    ansible-playbook \
        --connection=local \
        --inventory 127.0.0.1, \
        --limit 127.0.0.1 "${SCRIPT_DIR}/playbooks/install_comnetsemu.yml"
}

function all() {
    ansible_install_comnetsemu_localhost
}

function upgrade_comnetsemu() {
    warning "[Upgrade]" "Have you checked and merged the latest tag or release of the remote repository? ([y]/n)"
    read -r -n 1
    if [[ ! $REPLY ]] || [[ $REPLY =~ ^[Yy]$ ]]; then
        ansible_install_comnetsemu_localhost
    else
        error "[Upgrade]" "Please check and merge the latest tag or release of the remote repository before upgrading."
    fi
}

if [ $# -eq 0 ]; then
    usage
else
    while getopts 'ahu' option; do
        case $option in
        a) all ;;
        h) usage ;;
        u) upgrade_comnetsemu ;;
        *) usage ;;
        esac
    done
    shift "$((OPTIND - 1))"
fi

set +x
