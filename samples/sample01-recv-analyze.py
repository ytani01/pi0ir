import pigpio

from pi0ir import IrAnalyze, IrRecv


PIN = 24


def main():
    pi = pigpio.pi()  # pigpio 初期化

    receiver = IrRecv(pi, PIN)  # 赤外線信号受信オブジェクト
    analyzer = IrAnalyze()  # 赤外線信号解析オブジェクト

    try:  # 無限ループなので、終了するには、Ctrl-Cで強制終了
        while True:
            raw_data = receiver.recv()  # 赤外線信号の受信
            result = analyzer.analyze(raw_data)  # 生データを解析

            # 解析結果から、赤外線コードだけを抜き出して表示   
            button_str = result["buttons"]["button1"]
            if isinstance(button_str, list):
                button_str = button_str[0]
            button_code = button_str.lstrip('-').split('/')[0]
            print(f"{button_code}")

    except KeyboardInterrupt:  # Ctrl-Cを受け取り、スルーする
        pass
    
    finally:  # 終了処理
        receiver.end()
        pi.stop()
        print("\n END")

if __name__ == "__main__":
    main()
