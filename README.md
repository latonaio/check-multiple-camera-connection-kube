# check-multiple-camera-connection-kube
check-multiple-camera-connection-kubeは、USBで接続されたカメラ情報を検出します。

# 概要
本サービスは、USBで接続されている複数のカメラの接続情報を取得し、他マイクロサービスへ配信します。

配信はkanbanもしくはデータベースを通じて行われます。
*DBを通じた配信は現在非推奨になっております

配信されるデータは下記の二種類です。

- 接続されているデバイスのリスト
- 各デバイスのシリアル番号のリスト

デバイスのリストは`v4l2-ctl`コマンドを使用して取得されます。

# 動作環境
check-multiple-camera-connection-kubeはAIONのプラットフォーム上での動作を前提としています。 使用する際は、事前にAIONの動作環境を用意してください。   
- OS: Linux   
- CPU: Intel64/AMD64/ARM64   
- Kubernetes   
- AION   

`v4l2-ctl`コマンドがない場合は以下を実行して入手してください。

Debian系OSの場合
```
sudo apt install v4l-utils
```

# セットアップ
このリポジトリをクローンし、makeコマンドを用いてDocker container imageのビルドを行ってください。   
```
$ cd check-multiple-camera-connection-kube
$ make docker-build
```

## デプロイ on AION
AION上でデプロイする場合、project.yamlに次の設定を追加してください。
```
check-multiple-camera-connection:
    privileged: yes
    startup: yes   // aion起動時の立ち上げ設定
    always: yes    // 常時稼働
    env:
      MYSQL_USER: {user_name}
      MYSQL_PASSWORD: {password}
      KANBAN_ADDR: aion-statuskanban:10000
    nextService:
      default:
        - name: XXX //kanbanの監視下にある伝達先マイクロサービス
    volumeMountPathList:
      - /devices:/dev:Bidirectional
```

# I/O
### input
なし

### output
- device_list: 取得したデバイスリスト   
- devices: 各デバイスのシリアル番号のリスト