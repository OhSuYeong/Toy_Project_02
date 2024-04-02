# Toy_Project_02

## 인프라 구성 정리

- **on-premise 환경**
- **각 tool 버전 소개**

|  | version |
| --- | --- |
| Kubernetes | 1.28 |
| docker | 1.25 |
| Elasticsearch | 7.17.18 |
| kibana | 7.17.18 |
| Metricbeat | 7.17.19 |
| Jenkins | 2.440.1 |
| MariaDB | latest |
| Ansible | 2.16.2 |
- **각 노드의 환경**

| 구분 | ip | Prefix | 기본게이트웨이 | DNS | CPU/RAM | image |
| --- | --- | --- | --- | --- | --- | --- |
| master | 211.183.3.100 | /24 | 211.183.3.2 | 8.8.8.8 | 4/2 | ubuntu-20.04.4-desktop-amd64.iso |
| node1 | 211.183.3.101 | /24 | 211.183.3.2 | 8.8.8.8 | 2/2 | ubuntu-20.04.4-desktop-amd64.iso |
| node2 | 211.183.3.102 | /24 | 211.183.3.2 | 8.8.8.8 | 2/2 | ubuntu-20.04.4-desktop-amd64.iso |
| Jenkins | 211.183.3.99 | /24 | 211.183.3.2 | 8.8.8.8 | 2/2 | CentOS-Stream-8-20231218.0-x86_64-dvd |
| storage | 211.183.3.103 | /24 | 211.183.3.2 | 8.8.8.8 | 1/1 |  CentOS-7 x86_64-DVD-2009 |

---

## 1. Master node와 node1,2 기본 환경 셋팅

[master, node1, node2]

- vim 설치

```bash
sudo apt-get install vim
```

- /etc/sudoers 파일에 아래 내용 추가

```bash
user1  ALL=(ALL) NOPASSWD:ALL
```

- 도커 설치

```bash
$ sudo apt install apt-transport-https ca-certificates curl \
software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] \
https://download.docker.com/linux/ubuntu focal stable"
$ sudo apt-cache policy docker-ce
$ sudo apt install docker-ce -y
$ sudo systemctl enable docker
$ sudo systemctl restart docker
```

- 원격 접속을 위해 ssh 설치와 방화벽 기능 해제

<aside>
💡 ssh 설치한 뒤에 `SuperPuTTY` 실행하여 진행하는 것이 좀 더 편리함

</aside>

```bash
$ sudo apt-get install -y ssh
$ sudo systemctl enable ssh
$ sudo systemctl restart ssh
$ sudo ufw disable
```

- 스왑 메모리 비활성화

```bash
sudo swapoff -a
```

- /etc/fstab에서 swapfile 부분 주석 처리
- master와 node1을 위와 같이 진행한 후 node2를 clone

<aside>
💡 clone 시에 mac 주소를 다시 생성해야 하고 ipv4 address, hostname을 바꿔야함 + DNS 마찬가지

</aside>

```bash
$ hostname # hostname 확인
$ sudo hostnamectl set-hostname node2 # node1을 node2로 변경
```

```bash
root@node2:/home/user1# vi /etc/hosts
root@node2:/home/user1# sudo systemctl restart systemd-resolved
```

```yaml
# node2
127.0.0.1       localhost
127.0.1.1       node2 #이 부분이 node1으로 되어있을 것임 node2로 바꾸자

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

[master, node1, node2]

1. k8s 의 cgroup 드라이버를 리눅스 시스템과 동일하게 맞춰준다. (런타임이 도커라면)
도커의 cgroup 드라이버 이름 : cgroupfs
리눅스 시스템에서의 cgroup 드라이버 이름 : systemd
    
    Linux init 시스템의 cgroup 드라이버가 systemd인 경우, init 프로세스는 root control group(cgroup)을 생성 및 사용하는 cgroup 관리자로 작동합니다.
    
    Systemd는 cgroup과의 긴밀한 통합을 통해 프로세스당 cgroup을 할당합니다.
    
    이때 컨테이너 런타임과 kubelet이 cgroup 드라이버로 cgroupfs를 사용하도록 설정할 수 있습니다. 이는 linux 시스템이 사용하는 systemd와 함께 kubernetes kubelet이 사용하는 cgroupfs 드라이버를 서로 다른 cgroup 관리자가 관리하게 됩니다.
    
    ```bash
    cat <<EOF | sudo tee /etc/docker/daemon.json
    {
    	"exec-opts": ["native.cgroupdriver=systemd"]
    
    }
    EOF
    ```
    
    1. 아래의 파일을 실행
    
    ```bash
    #!/bin/bash
    # Add Docker's official GPG key:
    sudo apt remove containerd.io
    sudo apt-get update
    sudo apt-get install ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add the repository to Apt sources:
    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install containerd.io=1.6.24-1
    https://github.com/containernetworking/plugins/releases/download/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz
    sudo mkdir -p /opt/cni/bin
    sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.3.0.tgz
    sudo apt-get install -y kubelet=1.28.2-1.1 kubeadm=1.28.2-1.1 kubectl=1.28.2-1.1
    sudo apt-mark hold kubelet kubeadm kubectl
    
    sudo modprobe br_netfilter
    sudo modprobe overlay
    sudo sysctl -w net.ipv4.ip_forward=1
    
    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    EOF
    
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
    overlay
    br_netfilter
    EOF
    
    sudo sysctl --system
    
    containerd config default | sudo tee /etc/containerd/config.toml
    sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
    sudo systemctl restart containerd
    ```
    

3. master에서 kubeadm을 실행하여 클러스터 구성을 위한 토큰을 발행한다.(root)

[master, node1, node2]

```bash
kubeadm config images pull
kubeadm config images list
```

```bash
(아래는 master 에서만 진행)
kubeadm init --pod-network-cidr=10.244.0.0/16
```

1. master에서 클러스터가 시작되면 화면에 아래의 내용이 보인다. 복사하여 ‘붙여 넣기’ 한다. (root)

[master]

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=/etc/kubernetes/admin.conf

# export KUBECONFIG=/etc/kubernetes/admin.conf 은 ~/.bashrc 에 작성해둔다 껐다가 켜도 다시 되도록 환경변수 설정
```

1. kubectl → k로 간단히 설정

```bash
vi ~/.bashrc

alias k='kubectl'
```

```bash
source .bashrc
```

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

1. 화면에 보이는 토큰을 복사하여 각 노드에 붙여넣기 한다.

[node1,2]

```bash
kubeadm join 211.183.3.100:6443 --token p3lsj7.4a5vyxuqrck1yi6e \
        --discovery-token-ca-cert-hash sha256:dca2adf7e7c06ab2bdaa763e635f9f93fc45d6ba84475386855550e2b62d40e1
```

1. master 에서 kubernetes get node 를 확인한다.

```bash
root@master:~# kubectl get no
NAME     STATUS   ROLES           AGE     VERSION
master   Ready    control-plane   6m49s   v1.28.2
node1    Ready    <none>          99s     v1.28.2
node2    Ready    <none>          96s     v1.28.2
```

- 확인

```bash

root@master:~# k get no
NAME     STATUS     ROLES           AGE    VERSION
master   NotReady   control-plane   5m3s   v1.28.2
node1    NotReady   <none>          18s    v1.28.2
node2    NotReady   <none>          8s     v1.28.2
root@master:~# k get pod -n kube-system
NAME                             READY   STATUS    RESTARTS   AGE
coredns-5dd5756b68-fh9t4         1/1     Running   0          5m31s
coredns-5dd5756b68-qchhw         1/1     Running   0          5m31s
etcd-master                      1/1     Running   0          5m43s
kube-apiserver-master            1/1     Running   0          5m43s
kube-controller-manager-master   1/1     Running   0          5m43s
kube-proxy-fg8c8                 1/1     Running   0          49s
kube-proxy-gg4rb                 1/1     Running   0          5m31s
kube-proxy-rxmsv                 1/1     Running   0          59s
kube-scheduler-master            1/1     Running   0          5m43s

```

- 서비스 구성 전 사전 준비

```bash
root@master:~# vi /etc/ssh/sshd_config

 34 PermitRootLogin yes

root@master:~# systemctl restart sshd
```
![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/1d1f5e17-6d94-451c-9271-c698ee060384/71ff0973-8e2d-4eef-b79b-f730ed1ebee2/Untitled.png)