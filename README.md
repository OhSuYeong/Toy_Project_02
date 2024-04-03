# Toy_Project_02

## 인프라 구성 정리

- Backend 링크
  [GitHub - walloonam/backKakao](https://github.com/walloonam/backKakao/tree/main)
- Frontend 링크
  [GitHub - YoonHakyoung/myReact: React 활용한 Ticketing Web](https://github.com/YoonHakyoung/myReact)

  [GitHub - YoonHakyoung/Anemone: Docker Toy Project 2](https://github.com/YoonHakyoung/Anemone)

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
    
2. 아래의 파일을 실행
    
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

4. master에서 클러스터가 시작되면 화면에 아래의 내용이 보인다. 복사하여 ‘붙여 넣기’ 한다. (root)

[master]

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=/etc/kubernetes/admin.conf

# export KUBECONFIG=/etc/kubernetes/admin.conf 은 ~/.bashrc 에 작성해둔다 껐다가 켜도 다시 되도록 환경변수 설정
```

5. kubectl → k로 간단히 설정

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

6. 화면에 보이는 토큰을 복사하여 각 노드에 붙여넣기 한다.

[node1,2]

```bash
kubeadm join 211.183.3.100:6443 --token p3lsj7.4a5vyxuqrck1yi6e \
        --discovery-token-ca-cert-hash sha256:dca2adf7e7c06ab2bdaa763e635f9f93fc45d6ba84475386855550e2b62d40e1
```

7. master 에서 kubernetes get node 를 확인한다.

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
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/d563c78f-ba83-4a2e-be66-347b4bd95093)

- metallb 구성

```bash
1. kubectl edit configmap -n kube-system kube-proxy
 37     ipvs:
 41       strictARP: true    # <---- false 를 true 로 변경함

2. metallb 설치
 kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.10/config/manifests/metallb-native.yaml

(상태확인)
root@manager:~# k get pod -n metallb-system
NAME                          READY   STATUS    RESTARTS   AGE
controller-5c6b6c8447-twlhq   1/1     Running   0          48s
speaker-69l9b                 1/1     Running   0          48s
speaker-nq6xr                 1/1     Running   0          48s
speaker-w69vn                 1/1     Running   0          48s
root@manager:~#

3. pool 생성
root@manager:~# cat iprange.yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 211.183.3.201-211.183.3.239
root@manager:~#
root@manager:~# k apply -f iprange.yaml
root@manager:~# k get ipaddresspool -n metallb-system
NAME         AUTO ASSIGN   AVOID BUGGY IPS   ADDRESSES
first-pool   true          false             ["211.183.3.201-211.183.3.239"]
root@manager:~#

여기에서 오류 발생시 
# kubectl delete validatingwebhookconfigurations metallb-webhook-configuration 
이후 위를 다시 실행

추가적으로 L2 네트워크 생성 및 적용
root@manager:~# cat l2net.yaml
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: my-l2
  namespace: metallb-system
spec:
  ipAddressPools:
  - first-pool
root@manager:~# kubectl apply -f l2net.yaml
l2advertisement.metallb.io/my-l2 created
root@manager:~#
```

- 테스트 웹서버

[master node]

```bash
root@master:~# vi lbtest.yaml
root@master:~# k apply -f lbtest.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rapa-deploy-blue
spec:
  replicas: 1
  selector:
    matchLabels:
      color: blue  # "1"
  # 아래내용은 Pod 에 대한 구성내용
  template:
    metadata:
      name: rapa-pod-blue
      labels:
        color: blue  # 반드시 "1" 과 동일해야 함
    spec:
      containers:
        - name: rapa-ctn-blue
          image: brian24/rapaeng4:blue
          ports:
            - containerPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rapa-deploy-green
spec:
  replicas: 1
  selector:
    matchLabels:
      color: green  # "1"
  # 아래내용은 Pod 에 대한 구성내용
  template:
    metadata:
      name: rapa-pod-green
      labels:
        color: green  # 반드시 "1" 과 동일해야 함
    spec:
      containers:
        - name: rapa-ctn-green
          image: brian24/rapaeng4:green
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-rapaeng-lb
spec:
  ports:
  - name: web
    port: 80  #LB와 연결할 포트
    targetPort: 80
 
  selector:
    color: blue
  type: LoadBalancer
```

![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/07586a62-8cd3-4d7e-92a7-373818448cdf)

- 확인

```bash
root@master:~# k get svc,deploy
NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
service/kubernetes      ClusterIP      10.96.0.1       <none>          443/TCP        142m
service/my-rapaeng-lb   LoadBalancer   10.105.48.243   211.183.3.201   80:30914/TCP   8s

NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/rapa-deploy-blue    0/1     1            0           8s
deployment.apps/rapa-deploy-green   0/1     1            0           8s
root@master:~#

```

![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/1e1bc31b-2447-4ac8-95ac-04ed9c19a28f)

- 테스트 이후 삭제

```bash
root@master:~# k delete -f lbtest.yaml
```

<aside>
💡 렉이 너무 걸릴 경우를 대비해 run level을 5에서 3으로 아래와 같이 낮추는 것이 좋다.

</aside>

```bash
sudo systemctl isolate multi-user.target
sudo systemctl set-default multi-user.target
```

---

## 2. Jenkins Node 환경 설정

[Jenkins node]

1. CentOS 8로 설치 (minimal mode)로 설치

```bash
# vim 설치
sudo dnf -y install vim
```

- /etc/sudoers 파일에 아래 내용 추가

```bash
sudo vi /etc/sudoers

user1  ALL=(ALL) NOPASSWD:ALL
```

![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/35f9ecce-8877-40c4-a134-d03bf061c91f)

- 원격 접속을 위해 ssh 설치와 방화벽 기능 해제

<aside>
💡 ssh 설치한 뒤에 `SuperPuTTY` 실행하여 진행하는 것이 좀 더 편리함

</aside>

```bash
# OpenSSH 설치
sudo dnf -y install openssh-server

# SSH 서비스 활성화 및 재시작
sudo systemctl enable sshd
sudo systemctl restart sshd

# 방화벽 비활성화
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# root 계정 전환
su root
// 패스워드 : test123
```

2. jdk 설치 (root)

```bash
dnf -y install java-11-openjdk-devel
```

3. jenkins 설치 => 기본 저장소에서는 jenkins 설치를 지원하지 않는다. 따라서 jenkins repo. 를 직접 추가하고 설치해야 한다.

```bash
rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io-2023.key

cd /etc/yum.repos.d/

curl -O https://pkg.jenkins.io/redhat-stable/jenkins.repo
```

4. 설치

```bash
dnf -y install jenkins
```

5. 방화벽 해제

```bash
sudo systemctl stop firewalld
sudo systemctl disable firewalld
```

6. 시작

```bash
systemctl enable jenkins --now
```

7. 웹UI 를 통해 접속하기

[http://211.183.3.199:8080](http://211.183.3.199:8080/) 으로 접속하면 초기 패스워드 입력을 필요로 한다. 하지만 패스워드는 아직 없다. (아래의 코드를 입력하여 초기 패스워드 확인 가능)

```bash
cat /var/lib/jenkins/secrets/initialAdminPassword #초기 패스워드 확인 가능
```

8. 비밀번호를 입력하면 접속 가능

### git 설치가 안되어 있다면

```bash
# 경로 이동
[root@localhost ~]# cd /etc/yum.repos.d/

# git 설치 여부 확인
# 명령어 입력 후 출력 결과가 아무것도 안나온다면 git 설치가 안된 것
[root@localhost yum.repos.d]# rpm -qa git

# git 설치
[root@localhost yum.repos.d]# dnf -y install git
```

**도커 설치**

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
setenforce 0
systemctl disable firewalld  --now
systemctl enable docker --now
```

**ansible 설치하기**

```bash
dnf -y install epel-release
dnf -y install ansible
```

```bash
vi /etc/ansible/hosts
추가
master ansible_host=211.183.3.100
```

```bash
vi /etc/selinux/config
#SELINUXTYPE
selinux=disabled #로 바꿔 주기
```

**젠킨스 쉘 실행 권한 부여**

- 젠킨스가 쉘을 실행할 수 있는 권한이 없다.
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/6133ddb1-7f99-43d8-a552-063abeaebd54)
![/bin/false : 실행 권한 없음](https://prod-files-secure.s3.us-west-2.amazonaws.com/1d1f5e17-6d94-451c-9271-c698ee060384/d1661ac3-b709-4702-8692-0b2b44debfe8/Untitled.png)

/bin/false : 실행 권한 없음

```bash
# 젠킨스 실행 권한 여부 확인
cat /etc/passwd | grep jenkins

# 실행 권한 부여하기
# 권한 부여 후 제대로 변경이 됐는지 꼭 확인 필수!
usermod -s /bin/bash jenkins

```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/aef9287a-b538-4271-8141-d4a33069ff4f)

**젠킨스 root 권한 부여**

- root의 권한을 가지고 있지 않기 때문에 아래와 같이 추가 작업 필요하다

```bash
vi /etc/sudoers

jenkins         ALL=(ALL)       NOPASSWD: ALL
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/4354362f-7bde-4aa3-b6a1-37dc3bc0a81b)

**Docker 로그인 하기**

[jenkins node, master node]

```bash
[root@jenkins ~]# docker login
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/c012ac5c-befc-480a-9fd8-a48ff54c4b23)
**Jenkins와 master의 ssh 키페어 연결**

- jenkins 노드에서 jenkins로 접속

```bash
su jenkins
```

- jenkins 노드
    
    ```bash
    ssh-keygen -q -N "" -f jenkins.pem
    
    mkdir .ssh ; chmod 700 .ssh
    
    touch .ssh/known_hosts
    
    ssh-keyscan 211.183.3.100 >> .ssh/known_hosts
    ```
    
- master 노드
    
    ```bash
     mkdir .ssh ; chmod 700 .ssh
    
    touch .ssh/authorized_keys
    
    chmod 644 .ssh/authorized_keys
    
    vi .ssh/authorized_keys   # jenkins 의 pub 키를 저장시킨다
    ```
    
- jenkins 의 .ssh/config 에 클라이언트 설정을 작성

```bash
touch .ssh/config

chmod 644 .ssh/config

vi .ssh/config

Host master
HostName 211.183.3.100
User root
IdentityFile ~/jenkins.pem
```

- 접속 확인

```bash
ssh jenkins 'ls'
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/eee44799-c2a1-4e43-9461-64ecedc9a8ca)
<aside>
💡 혹시 permission error 혹은 password 입력하라는 오류가 뜬다면 다음과 같은 환경을 확인하세요

</aside>

[master node]

```bash
root@master:~# vi /etc/ssh/ssh_config

 25    PasswordAuthentication yes
 26    HostbasedAuthentication yes
```

---

## 3. Elasticsearch & Kibana & Metricbeat Kubernetes로 배포

- 기본 port : `Elasticserarch`는 9200 port, `Kibana`는 5601 port (둘 다 TCP)
- 기본적으로 127.0.0.1 으로 되어 있기에 원격으로는 접속이 안 된다. (0.0.0.0 (any)로 변경)
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/d90e4a02-5fd8-4eba-af40-4ed5310ad00b)
- Elasticsearch 7.17.x → 모든 CentOS와 Ubuntu 버전 지원

### 스토리지 구성

211.183.3.103 storage server 만들고 storage 와 master worker 1, 2 에 각각 알맞게 명령어 실행

**초기 환경 구성**

```bash
sudo yum install openssh-server
sudo systemctl start sshd
sudo systemctl enable sshd

sudo firewall-cmd --zone=public --add-port=22/tcp --permanent
sudo firewall-cmd --reload
```

방화벽 끄기

```bash
sudo systemctl stop firewalld
sudo systemctl disable firewalld
sudo systemctl status firewalld
● firewalld.service - firewalld - dynamic firewall daemon
   Loaded: loaded (/usr/lib/systemd/system/firewalld.service; disabled; vendor preset: enabled)
   Active: inactive (dead)
     Docs: man:firewalld(1)

Mar 27 13:52:41 storage systemd[1]: Starting firewalld - dynamic firew....
Mar 27 13:52:42 storage systemd[1]: Started firewalld - dynamic firewa....
Mar 27 13:52:42 storage firewalld[705]: WARNING: AllowZoneDrifting is ....
Mar 27 14:08:01 storage firewalld[705]: WARNING: AllowZoneDrifting is ....
Mar 27 16:04:07 storage systemd[1]: Stopping firewalld - dynamic firew....
Mar 27 16:04:08 storage systemd[1]: Stopped firewalld - dynamic firewa....
Hint: Some lines were ellipsized, use -l to show in full.
```

```bash
#stroage
sudo yum install nfs-utils

#master, worker1,woker2
sudo apt install nfs-common
sudo systemctl enable rpcbind --now
```

stroage 서버에서

```bash
#storage
cat /etc/exports
/nfs *(rw,sync,no_root_squash)

mkdir /nfs
chmod 777 /nfs

systemctl enable nfs --now
```

방화벽 체크 후 해제

```bash
# node1, node2
sudo systemctl disable ufw
```

### Elasticsearch Deployment 배포

- 네임스페이스 확인 후 생성

```bash
kubectl get namespaces

kubectl create namespace elk
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/af9e500f-6d38-4339-97cb-df9f7494ecce)
[master node]

**elkpv.yaml**

```bash
# elkpv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: elasticsearch-pv
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  nfs:
    path: /nfs  # NFS 서버의 경로로 변경해야 합니다.
    server: 211.183.3.103  # NFS 서버의 IP 주소로 변경해야 합니다.

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: elasticsearch-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

결과

```bash
root@master:~/elk# k apply -f elkpv.yaml
persistentvolume/elasticsearch-pv created
persistentvolumeclaim/elasticsearch-pvc created
```

```bash
root@master:~/elk# k get pv,pvc
NAME                                CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                       STORAGECLASS   REASON   AGE
persistentvolume/elasticsearch-pv   10Gi       RWO            Retain           Bound    default/elasticsearch-pvc                           11s

NAME                                      STATUS   VOLUME             CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/elasticsearch-pvc   Bound    elasticsearch-pv   10Gi       RWO                           11s
```

**elk.yaml**

```bash
# elk.yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  labels:
    app: elasticsearch
spec:
  type: NodePort  # 변경
  ports:
    - name: http
      port: 9200
      targetPort: 9200
      nodePort: 30001  # 추가
  selector:
    app: elasticsearch

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
spec:
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.18
        env:
          - name: node.name
            value: single
          - name: cluster.name
            value: standalone
          - name: discovery.type
            value: single-node
          # - name: ES_JAVA_OPTS
            # value: "-Xms1g -Xmx1g -Djava.security.manage=false"
        volumeMounts:
          # - name: config
          #   mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
          #   subPath: elasticsearch.yml
          - name: data
            mountPath: /usr/share/elasticsearch/data
        ports:
          - containerPort: 9200
      volumes:
        # - name: config
        #   configMap:
        #     name: elasticsearch-config
        - name: data
          persistentVolumeClaim:
            claimName: elasticsearch-pvc

```

결과

```bash
root@master:~/elk# k apply -f elk.yaml
service/elasticsearch created
deployment.apps/elasticsearch created
```

<aside>
💡 pod 생성은 시간이 걸리므로 -w 옵션으로 확인하는 게 더 좋음

</aside>

결과

```bash
root@master:~/elk# k get pod -w
NAME                             READY   STATUS              RESTARTS   AGE
elasticsearch-7fcb7ff58d-bmp94   0/1     ContainerCreating   0          9s
elasticsearch-7fcb7ff58d-bmp94   1/1     Running             0          26s
```

### Kibana deployment 배포

**kibana.yaml**

```bash
#kibana.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: kibana
  labels:
    app: kibana
spec:
  type: NodePort  # 변경
  ports:
    - name: http
      port: 5601
      targetPort: 5601
      nodePort: 30002  # 추가
  selector:
    app: kibana
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.17.18
        env:
          - name: ELASTICSEARCH_HOSTS
            value: http://elasticsearch:9200
        ports:
          - containerPort: 5601
```

결과

```bash
root@master:~/elk# k apply -f kibana.yaml
service/kibana created
deployment.apps/kibana created
```

```bash
root@master:~/elk# k get pod
NAME                             READY   STATUS    RESTARTS   AGE
elasticsearch-7fcb7ff58d-bmp94   1/1     Running   0          8m54s
kibana-86b787664d-s7smh          1/1     Running   0          89s
```

```bash
root@master:~/elk# k get svc
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
elasticsearch   NodePort    10.108.119.30   <none>        9200:30001/TCP   9m18s
kibana          NodePort    10.104.185.19   <none>        5601:30002/TCP   113s
kubernetes      ClusterIP   10.96.0.1       <none>        443/TCP          9d
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/7d36e948-b69b-4ffd-be81-ccc77a0227e2)
### MetricBeat Daemonset 배포

<aside>
💡 image 존재 확인
https://www.docker.elastic.co/r/kibana/kibana?limit=50&offset=100&show_snapshots=false

</aside>

**metricbeat-kubernetes.yaml**

```bash
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: metricbeat-daemonset-config
  namespace: kube-system
  labels:
    k8s-app: metricbeat
data:
  metricbeat.yml: |-
    metricbeat.config.modules:
      # Mounted `metricbeat-daemonset-modules` configmap:
      path: ${path.config}/modules.d/*.yml
      # Reload module configs as they change:
      reload.enabled: false

    metricbeat.autodiscover:
      providers:
        - type: kubernetes
          scope: cluster
          node: ${NODE_NAME}
          # In large Kubernetes clusters consider setting unique to false
          # to avoid using the leader election strategy and
          # instead run a dedicated Metricbeat instance using a Deployment in addition to the DaemonSet
          unique: true
          templates:
            - config:
                # - module: kubernetes
                #   hosts: ["kube-state-metrics:8080"]
                #   period: 10s
                #   add_metadata: true
                #   metricsets:
                #     - state_node
                #     - state_deployment
                #     - state_daemonset
                #     - state_replicaset
                #     - state_pod
                #     - state_container
                #     - state_job
                #     - state_cronjob
                #     - state_resourcequota
                #     - state_statefulset
                #     - state_service
                - module: kubernetes
                  metricsets:
                    - apiserver
                    - node
                    - system
                    - pod
                    - container
                    - volume
                  hosts: ["https://kubernetes.default.svc.cluster.local:443"]
                  bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
                  ssl.certificate_authorities:
                    - /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
                  period: 30s
                # Uncomment this to get k8s events:
                #- module: kubernetes
                #  metricsets:
                #    - event
        # To enable hints based autodiscover uncomment this:
        #- type: kubernetes
        #  node: ${NODE_NAME}
        #  hints.enabled: true

    processors:
      - add_cloud_metadata:

    cloud.id: ${ELASTIC_CLOUD_ID}
    cloud.auth: ${ELASTIC_CLOUD_AUTH}

    output.elasticsearch:
      hosts: ["elasticsearch.default.svc.cluster.local:9200"] # Elasticsearch 호스트 및 포트
      username: "elasticsearch" # Elasticsearch 인증 정보 (선택 사항)
      password: "test123" # Elasticsearch 인증 정보 (선택 사항)
    
    setup.dashboards:
      enabled: true
    
    setup.kibana:
      host: "http://kibana.default.svc.cluster.local:5601"
      username: "elasticsearch"
      password: "test123"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: metricbeat-daemonset-modules
  namespace: kube-system
  labels:
    k8s-app: metricbeat
data:
  system.yml: |-
    - module: system
      period: 10s
      metricsets:
        - cpu
        - load
        - memory
        - network
        - process
        - process_summary
        #- core
        #- diskio
        #- socket
      processes: ['.*']
      process.include_top_n:
        by_cpu: 5      # include top 5 processes by CPU
        by_memory: 5   # include top 5 processes by memory

    - module: system
      period: 1m
      metricsets:
        - filesystem
        - fsstat
      processors:
      - drop_event.when.regexp:
          system.filesystem.mount_point: '^/(sys|cgroup|proc|dev|etc|host|lib|snap)($|/)'
  kubernetes.yml: |-
    - module: kubernetes
      metricsets:
        - node
        - system
        - pod
        - container
        - volume
      period: 10s
      host: ${NODE_NAME}
      hosts: ["https://${NODE_NAME}:10250"]
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      ssl.verification_mode: "none"
      # If there is a CA bundle that contains the issuer of the certificate used in the Kubelet API,
      # remove ssl.verification_mode entry and use the CA, for instance:
      #ssl.certificate_authorities:
        #- /var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt
    # Currently `proxy` metricset is not supported on Openshift, comment out section
    - module: kubernetes
      metricsets:
        - proxy
      period: 10s
      host: ${NODE_NAME}
      hosts: ["localhost:10249"]
---
# Deploy a Metricbeat instance per node for node metrics retrieval
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: metricbeat
  namespace: kube-system
  labels:
    k8s-app: metricbeat
spec:
  selector:
    matchLabels:
      k8s-app: metricbeat
  template:
    metadata:
      labels:
        k8s-app: metricbeat
    spec:
      serviceAccountName: metricbeat
      terminationGracePeriodSeconds: 30
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: metricbeat
        image: docker.elastic.co/beats/metricbeat:7.17.19
        args: [
          "-c", "/etc/metricbeat.yml",
          "-e",
          "-system.hostfs=/hostfs",
        ]
        env:
        - name: ELASTICSEARCH_HOST
          value: elasticsearch
        - name: ELASTICSEARCH_PORT
          value: "9200"
        - name: ELASTICSEARCH_USERNAME
          value: elastic
        - name: ELASTICSEARCH_PASSWORD
          value: test123
        - name: ELASTIC_CLOUD_ID
          value:
        - name: ELASTIC_CLOUD_AUTH
          value:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        securityContext:
          runAsUser: 0
          # If using Red Hat OpenShift uncomment this:
          #privileged: true
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 100Mi
        volumeMounts:
        - name: config
          mountPath: /etc/metricbeat.yml
          readOnly: true
          subPath: metricbeat.yml
        - name: data
          mountPath: /usr/share/metricbeat/data
        - name: modules
          mountPath: /usr/share/metricbeat/modules.d
          readOnly: true
        - name: proc
          mountPath: /hostfs/proc
          readOnly: true
        - name: cgroup
          mountPath: /hostfs/sys/fs/cgroup
          readOnly: true
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: cgroup
        hostPath:
          path: /sys/fs/cgroup
      - name: config
        configMap:
          defaultMode: 0640
          name: metricbeat-daemonset-config
      - name: modules
        configMap:
          defaultMode: 0640
          name: metricbeat-daemonset-modules
      - name: data
        hostPath:
          # When metricbeat runs as non-root user, this directory needs to be writable by group (g+w)
          path: /var/lib/metricbeat-data
          type: DirectoryOrCreate
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: metricbeat
subjects:
- kind: ServiceAccount
  name: metricbeat
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: metricbeat
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: metricbeat
  namespace: kube-system
subjects:
  - kind: ServiceAccount
    name: metricbeat
    namespace: kube-system
roleRef:
  kind: Role
  name: metricbeat
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: metricbeat-kubeadm-config
  namespace: kube-system
subjects:
  - kind: ServiceAccount
    name: metricbeat
    namespace: kube-system
roleRef:
  kind: Role
  name: metricbeat-kubeadm-config
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: metricbeat
  labels:
    k8s-app: metricbeat
rules:
- apiGroups: [""]
  resources:
  - nodes
  - namespaces
  - events
  - pods
  - services
  verbs: ["get", "list", "watch"]
# Enable this rule only if planing to use Kubernetes keystore
#- apiGroups: [""]
#  resources:
#  - secrets
#  verbs: ["get"]
- apiGroups: ["extensions"]
  resources:
  - replicasets
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources:
  - statefulsets
  - deployments
  - replicasets
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources:
  - jobs
  verbs: ["get", "list", "watch"]
- apiGroups:
  - ""
  resources:
  - nodes/stats
  verbs:
  - get
- nonResourceURLs:
  - "/metrics"
  verbs:
  - get
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: metricbeat
  # should be the namespace where metricbeat is running
  namespace: kube-system
  labels:
    k8s-app: metricbeat
rules:
  - apiGroups:
      - coordination.k8s.io
    resources:
      - leases
    verbs: ["get", "create", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: metricbeat-kubeadm-config
  namespace: kube-system
  labels:
    k8s-app: metricbeat
rules:
  - apiGroups: [""]
    resources:
      - configmaps
    resourceNames:
      - kubeadm-config
    verbs: ["get"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: metricbeat
  namespace: kube-system
  labels:
    k8s-app: metricbeat
---
- 모든 네임스페이스의 모든 파드 확인

```bash
kubectl get pods --all-namespaces
```
```
## 3. 대쉬 보드 커스터마이징
![1](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/bd47c90f-aac7-433f-8412-8afe7828eeb7)
![2](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/ac0b187c-7562-466e-a647-b4a600b93769)
![3](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/3f88bec4-e797-4c7f-8ab3-f0081da98db9)
![4](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/3e3dcb45-ccc5-413d-b864-0aa6bb7aa998)
![5](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/e5419d62-9561-4641-9149-9ba74cd173dd)
![6](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/2e096819-0052-4abb-8cb6-e53eb3360083)
![7](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/954efba1-5fa7-4346-8bd9-e89f6a6b6ff1)
![8](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/e21d5067-b952-43e1-a18f-bd190ebd18d8)
![9](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/1f26f69a-c6a1-424f-bde1-aefca61f1a94)
![10](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/88a3eb45-57cc-4891-9016-0c2e751ac340)
![11](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/4ea8a14e-2b71-4d7b-a35d-c40c6798c671)
![12](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/3fb3989c-2851-4c68-bd88-cd1ce62b28f3)

---

## 4. storage 노드 Raid (s3)

**RAID1 선택한 이유**

1. **높은 데이터 안정성**: RAID 1은 데이터의 완전한 복제본을 유지하기 때문에 한 개의 디스크가 손상되어도 나머지 디스크에 있는 데이터로 서비스를 계속할 수 있다. 이는 데이터의 손실을 방지하고 시스템의 가용성을 높인다. 디스크 하나의 고장으로 인해 시스템이 중단되는 상황을 피할 수 있다.
2. **간편한 데이터 복구**: RAID 1에서는 손상된 디스크를 교체하고 다른 디스크에 있는 데이터를 복제하는 것으로 데이터를 복구할 수 있다. 이는 데이터의 손실을 최소화하고 서비스 복구 시간을 단축할 수 있다. 따라서 시스템 관리자가 복잡한 복구 절차를 수행할 필요가 없다.
3. **상대적으로 높은 읽기 성능**: RAID 1은 데이터를 복제하여 여러 디스크에 분산시키지 않고 동시에 여러 디스크에서 데이터를 읽을 수 있습니다. 이는 읽기 작업의 병렬 처리를 가능하게 하여 읽기 성능을 향상시킬 수 있다. 특히 읽기 중심의 작업에서 성능 향상을 경험할 수 있다.
4. **간단한 구성 및 관리**: RAID 1은 미러링만으로 구성되기 때문에 구성이 간단합니다. 미러링은 데이터의 복제만 수행하므로 추가적인 패리티 계산이 필요하지 않습니다. 이는 시스템 구성 및 관리를 단순화하고 유지보수 비용을 절감할 수 있다.

RAID 1은 미러링을 통해 데이터의 안정성을 제공하므로, 데이터 백업과 복구에 중점을 둔다면 다른 RAID 레벨보다 좋은선택이다.

| 구분 | ip | Prefix | 기본게이트웨이 | DNS | CPU/RAM |  |
| --- | --- | --- | --- | --- | --- | --- |
| storage | 211.183.3.103 | /24 | 211.183.3.2 | 8.8.8.8 | 1/1 |  |
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/688f9b57-f566-4cda-afdd-9214b59e2f03)
Edit 을 누르고 원래 있는 하드 디스크를 삭제후 Add 버튼을 누르고 Hard disk 생성
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/e639faa2-f3e6-49c9-b317-938ae61398ad)
SCSI 로 생성해야함!
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/ad8054c3-4710-453c-ad5b-18cdb44d8b16)
※ 20GB로 설치를 먼저 해야함!

설치가 끝난 뒤 ip 확인후 정지 시킨 뒤 

Edit 을 눌러 다시 hard disk 생성 그 때 size는 5GB로 정하고 mutiple files로 통일해서 2개 만든다.
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/ef15b6fd-d006-4555-ba85-b3eed5dd6727)

이렇게 3개 SCSI가 있어야 한다.
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/9f3bf93d-1ad3-40f7-a066-86f7262b178b)

새로 추가 시킨 2개의 디스크가 dev/sdb , dev/sdc로 마운트 되어 있는지 확인한다.
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/ba9f0a7d-bb4a-4f90-a090-e70f70a28c3d)
| # mdadm 설치 (Ubuntu/Debian 기반 시스템의 경우)
sudo apt update && sudo apt install mdadm -y

# RAID 어레이 생성 (/dev/md0으로 생성됩니다)
sudo mdadm --create --verbose /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc

# 생성된 RAID 어레이에 대한 정보를 확인합니다.
sudo mdadm --detail /dev/md0

# 파일 시스템 생성 (ext4를 예로 들었습니다)
sudo mkfs.ext4 /dev/md0

# 마운트할 디렉토리 생성
sudo mkdir -p /mnt/raid1

# RAID 어레이를 시스템에 마운트
sudo mount /dev/md0 /mnt/raid1

# 부팅 시 자동 마운트를 위해 /etc/fstab에 추가
echo '/dev/md0 /mnt/raid1 ext4 defaults,nofail,discard 0 0' | sudo tee -a /etc/fstab

# mdadm 구성 파일 업데이트
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
sudo update-initramfs -u
 |
| --- |

**마운트된 파일 시스템 확인하기**

- df -h 또는
- mount | grep /mnt/raid1

---

## 5. Jenkins로 Web server, DB 배포

### pod 배포 (master)

---

- web.yaml

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myweb
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myweb
  template:
    metadata:
      labels:
        app: myweb
    spec:
      containers:
      - name: myweb
        image: yoonhakyoung/anemone:new-ver
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: myweb-service
spec:
  selector:
    app: myweb
  ports:
    - protocol: TCP
      port: 3000
      targetPort: 3000
  type: NodePort
```
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/547c5e9c-f647-4efd-916b-0b5a817a9906)
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/9ebbc6fa-41c6-4aa5-9fd9-e6ca94714ea8)
### Jenkins로 배포

---

- Jenkins Node
    
    ```bash
    mkdir myGit
    cd myGit
    git init
    git clone https://github.com/YoonHakyoung/myReact.git
    ```
    
- Jenkins Web 접속
    - http://211.183.3.99:8080/
    - ID : admin
    PW : test123
    
- 새로운 item 생성
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/3af01c0b-d2c9-45f1-8bbe-c3642ddc3adb)
- item명 : myWeb
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/d711cdf4-c0a5-4a96-b433-e6d20a981717)
- 깃 연결
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/d8c9b551-1b5c-4d40-bb50-20aa6eda815f)

    
    ```bash
    https://github.com/YoonHakyoung/myReact.git
    ```
    
    - 브랜치명 main으로 변경
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/f6f33970-b925-466b-b2b9-14e6b63e3dea)
- build step
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/a00e47fc-3d0c-4294-b320-90a2fcea60e9)

    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/22d68b98-0e8b-4bf5-8dec-a52e1eb12245)

    
    ```bash
    cd /var/lib/jenkins/myGit/myReact
    git pull
    sudo docker build -t yoonhakyoung/anemone:new-ver .
    sudo docker push yoonhakyoung/anemone:new-ver
    ansible master -m shell -a 'kubectl apply -f web.yaml'
    ```
- 지금 빌드
    
    ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/c17c3f50-9654-4146-9d9c-7100e26fec68)
- 배포 확인 (master)
  ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/d7a84183-d7c9-46a7-999a-961bb79b0e7a)
  ![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/4797f1e6-264c-4d7f-90e8-097be432ecb8)
### db 배포(db.yaml)

```bash

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:latest
          env:
            - name: MYSQL_ROOT_PASSWORD
              value: "test123"
            - name: MYSQL_ROOT_HOST
              value: "%"
          ports:
            - containerPort: 3306

---

apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
    - protocol: TCP
      port: 3306
      targetPort: 3306
      nodePort: 30001 # 임의의 NodePort 번호를 선택하세요

```

---

## 5. Jenkins-Slack 연동

실행화면
![Untitled](https://github.com/OhSuYeong/Toy_Project_02/assets/101083171/13887cca-3242-48ad-a464-a5f47bf99888)
- slackAPI.py

```python
# -*- coding: utf-8 -*-

from flask import Flask, request
from slack_sdk import WebClient
import re
import sys
import jenkins
import time
import requests

# Jenkins 서버 URL 및 자격 증명 설정
jenkins_url = 'http://localhost:8080'
username = 'admin'
password = 'test123'

# Jenkins 객체 생성
server = jenkins.Jenkins(jenkins_url, username=username, password=password)

app = Flask(__name__)

class SlackAPI:
    """
    슬랙 API 핸들러
    """
    def __init__(self, token):
        self.client = WebClient(token)
        
    def get_channel_id(self, channel_name):
        """
        슬랙 채널ID 조회
        """
        result = self.client.conversations_list()
        channels = result.data['channels']
        filtered_channels = list(filter(lambda c: c["name"] == channel_name, channels))
        if filtered_channels:
            channel = filtered_channels[0]
            # 채널ID 파싱
            channel_id = channel["id"]
            return channel_id
        else:
            print(f"Channel '{channel_name}' not found. Shut down the server.")
            sys.exit(1)  # 서버 종료, 종료 코드 1 반환

    def get_latest_message(self, channel_id):
        """
        슬랙 채널 내 메세지 조회
        """
        # conversations_history() 메서드 호출
        result = self.client.conversations_history(channel=channel_id)

        # 채널 내 메세지 정보 딕셔너리 리스트
        messages = result.data['messages']

        # 마지막 메세지
        message = messages[0]

        msg = None

        # github 커밋 메세지일 때
        if 'bot_id' in message and message['bot_id'] == 'B06RCGCUJQN':
            text = message['attachments'][0]['fallback']

            # 정규 표현식 패턴
            pattern = r'\[(.*?)\:(.*?)\]'
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if match[0] == 'myReact':
                        msg = "🚀 프론트엔드에서 새로운 커밋이 발생하였습니다. \n 배포를 원하실 경우 '프론트엔드 배포'라고 입력해주세요!"
                    elif match[0] == 'backKakao':
                        msg = "🚀 백엔드에서 새로운 커밋이 발생하였습니다. \n 배포를 원하실 경우 '백엔드 배포'라고 입력해주세요!"
                    else:
                        print(f"This is not a commit message. Shut down the server.")
                        sys.exit(1)  # 서버 종료, 종료 코드 1 반환
            else: 
                print(f"This is not a commit message. Shut down the server.")
                sys.exit(1)  # 서버 종료, 종료 코드 1 반환

        # 프론트엔드 배포 메세지일 때
        elif 'text' in message and message['text'] == '프론트엔드 배포':
            self.post_message("C06R4JFPHPH", "🚀 프론트엔드 배포를 시작합니다.")
            # Jenkins 작업 가져오기
            job_name = 'myWeb'
            # 작업 빌드
            server.build_job(job_name)

            self.get_build_console_output(jenkins_url, job_name, username, password)

            msg = "🎉 프론트엔드 배포가 성공적으로 완료되었습니다!"

        
        # 백엔드 배포 메세지일 때
        elif 'text' in message and message['text'] == '백엔드 배포':
            msg = "🚀 백엔드 배포를 시작합니다."
            msg ="백엔드배포 완료"

        return msg

    def post_message(self, channel_id, msg):
        """
        슬랙 채널에 메세지 보내기
        """
        # chat_postMessage() 메서드 호출
        result = self.client.chat_postMessage(channel=channel_id, text=msg)
        return result

    # Jenkins 서버 API로 빌드 중인 작업의 콘솔 출력 가져오기
    def get_build_console_output(self, server_url, job_name, username, password):
        url = f"{server_url}/job/{job_name}/lastBuild/logText/progressiveText"
        headers = {'Accept': 'text/plain'}
        session = requests.Session()
        session.auth = (username, password)
        
        try:
            while True:
                response = session.get(url, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        # print(line)
                        if line.strip().startswith("+ git pull"):
                            self.post_message("C06R4JFPHPH", "> 새로운 커밋 적용")
                        elif line.strip().startswith("+ sudo docker build"):
                            self.post_message("C06R4JFPHPH", "> 이미지 빌드 중 ...")
                        elif line.strip().startswith("+ sudo docker push"):
                            self.post_message("C06R4JFPHPH", "> 이미지 푸시 중 ...")
                        elif line.strip().startswith("+ ansible"):
                            self.post_message("C06R4JFPHPH", "> 배포 중 ...")
                        elif line.strip() == "Finished: SUCCESS":
                            return  # 빌드가 성공적으로 완료되면 함수 종료
        except requests.exceptions.Timeout:
            print("Timeout occurred. Retrying...")
            get_build_console_output(server_url, job_name, username, password)
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)

def send_message_periodically():
    while True:
        # SlackAPI 인스턴스를 만듭니다.
        slack_api = SlackAPI(token='개인정보 보호')
        
        # 채널 이름
        # channel_name = "cicd"
        
        # 채널 ID 파싱
        # channel_id = slack_api.get_channel_id(channel_name)
        channel_id = "C06R4JFPHPH"
        
        # 메시지 파싱
        msg = slack_api.get_latest_message(channel_id)

        time.sleep(5)

        # 메세지 전송
        if msg != None:
            slack_api.post_message(channel_id, msg)

send_message_periodically()

@app.route('/slack/message', methods=['POST'])
def handle_message():
    # 슬랙에서의 요청을 받습니다.
    data = request.json
    # 요청에 대한 응답을 반환합니다.
    return 'Message handled successfully!', 200

if __name__ == '__main__':
    app.run(debug=True)
```
