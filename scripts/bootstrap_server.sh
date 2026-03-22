#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

deploy_user="${DEPLOY_USER:-deploy}"
deploy_home="/home/${deploy_user}"
repo_dir="${REPO_DIR:-/opt/cleair}"
timezone_name="${TIMEZONE_NAME:-UTC}"
swap_size_gb="${SWAP_SIZE_GB:-2}"
ssh_dir="${deploy_home}/.ssh"

if ! [[ "${swap_size_gb}" =~ ^[0-9]+$ ]] || [[ "${swap_size_gb}" -lt 1 ]]; then
    echo "SWAP_SIZE_GB must be a positive integer."
    exit 1
fi

install_base_packages() {
    export DEBIAN_FRONTEND=noninteractive
    apt update
    apt upgrade -y -o Dpkg::Options::="--force-confold"
    apt install -y ca-certificates curl gnupg ufw rsync
}

set_timezone() {
    timedatectl set-timezone "${timezone_name}"
}

ensure_deploy_user() {
    local sudoers_file="/etc/sudoers.d/90-${deploy_user}"

    if ! id -u "${deploy_user}" >/dev/null 2>&1; then
        adduser --disabled-password --gecos "" "${deploy_user}"
    fi

    usermod -aG sudo "${deploy_user}"
    printf '%s ALL=(ALL) NOPASSWD:ALL\n' "${deploy_user}" > "${sudoers_file}"
    chmod 440 "${sudoers_file}"

    if [[ -f /root/.ssh/authorized_keys && ! -e "${ssh_dir}/authorized_keys" ]]; then
        mkdir -p "${ssh_dir}"
        install -m 600 /root/.ssh/authorized_keys "${ssh_dir}/authorized_keys"
        chown -R "${deploy_user}:${deploy_user}" "${ssh_dir}"
        chmod 700 "${ssh_dir}"
    fi

    if [[ -d "${repo_dir}" ]]; then
        chown -R "${deploy_user}:${deploy_user}" "${repo_dir}"
    fi
}

configure_firewall() {
    ufw allow OpenSSH
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
}

install_docker() {
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] " \
        "https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    usermod -aG docker "${deploy_user}"
    systemctl enable docker
    systemctl start docker
}

configure_swap() {
    if swapon --show=NAME --noheadings | grep -qx /swapfile; then
        return
    fi

    if [[ -e /swapfile ]]; then
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile

        if ! grep -q '^/swapfile none swap sw 0 0$' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
        fi

        return
    fi

    fallocate -l "${swap_size_gb}G" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile

    if ! grep -q '^/swapfile none swap sw 0 0$' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
}

print_summary() {
    cat <<EOF
Bootstrap complete.

Deploy user: ${deploy_user}
Repo dir: ${repo_dir}
Timezone: ${timezone_name}
Swap: ${swap_size_gb}G

Next steps:
1. Log in as ${deploy_user}.
2. Ensure ${repo_dir} is available for future deploys.
3. Add the deploy SSH key for ${deploy_user}.
4. Set GitHub Actions deploy variables and secrets, then trigger the Deploy workflow.
5. After confirming key-based login works for ${deploy_user}, harden SSH manually.
EOF
}

install_base_packages
set_timezone
ensure_deploy_user
configure_firewall
install_docker
configure_swap
print_summary
