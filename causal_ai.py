import os
import pandas as pd
import numpy as np
import dowhy
from dowhy import CausalModel
import matplotlib.pyplot as plt
import seaborn as sns

# 현재 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# 현물과 선물 데이터 로드
spot_df = pd.read_csv(os.path.join(current_dir, 'binance_1m_BTCUSDT.csv'))
future_df = pd.read_csv(os.path.join(current_dir, 'binance_1m_BTCUSDT_f.csv'))

# 컬럼명 변경
spot_df.columns = ['timestamp', 'spot_open', 'spot_high', 'spot_low', 'spot_close', 'spot_volume']
future_df.columns = ['timestamp', 'future_open', 'future_high', 'future_low', 'future_close', 'future_volume']

# timestamp를 기준으로 데이터 병합
merged_df = pd.merge(future_df, spot_df, on='timestamp', how='inner')
merged_df = merged_df.dropna()

# 가격 변화율 계산
merged_df['spot_returns'] = merged_df['spot_close'].pct_change()
merged_df['future_returns'] = merged_df['future_close'].pct_change()
merged_df = merged_df.dropna()

# 시차 변수 생성
def create_lagged_vars(df, vars=['spot_returns', 'future_returns'], lags=5):
    temp_df = df.copy()
    
    for var in vars:
        for lag in range(1, lags+1):
            temp_df[f'{var}_lag{lag}'] = temp_df[var].shift(lag)
    
    return temp_df.dropna()

# 데이터 준비
lagged_df = create_lagged_vars(merged_df)

# DoWhy를 사용한 인과관계 분석
print("\n=== DoWhy를 사용한 인과관계 분석 시작 ===")

# 인과 모델 정의
model_spec = """
treatment: spot_returns
outcome: future_returns
common_causes: ['spot_volume', 'future_volume']
"""

causal_model = CausalModel(
    data=lagged_df,
    treatment='spot_returns_lag1',
    outcome='future_returns',
    # common_causes=['spot_volume', 'future_volume'],
    # instruments=['spot_returns_lag2', 'spot_returns_lag3'],
    # effect_modifiers=['spot_volume', 'future_volume']
)

# 인과 그래프 식별
identified_estimand = causal_model.identify_effect(proceed_when_unidentifiable=True)

# 인과 효과 추정
estimate = causal_model.estimate_effect(identified_estimand,
                                      method_name="backdoor.linear_regression")

# 리포트 출력
print("\n=== 인과관계 분석 결과 ===")
print(estimate)

# # 리포트 시각화
# plt.figure(figsize=(12, 8))
# print("됨?")
# sns.regplot(data=lagged_df, x='spot_returns_lag1', y='future_returns')
# plt.title("현물 수익률과 선물 수익률의 관계")
# plt.xlabel("현물 수익률")
# plt.ylabel("선물 수익률")
# plt.savefig("causal_analysis.png")
# plt.close()

# 강건성 검정
refutation_results = causal_model.refute_estimate(identified_estimand, estimate,
                                                method_name="random_common_cause")

print("\n=== 강건성 검정 결과 ===")
print(refutation_results)

# 결과 저장
with open('causal_analysis_report.txt', 'w', encoding='utf-8') as f:
    f.write("=== BTC 현물/선물 인과관계 분석 보고서 ===\n\n")
    f.write(str(estimate))
    f.write("\n\n=== 강건성 검정 결과 ===\n")
    f.write(str(refutation_results))

print("\n분석 결과가 'causal_analysis_report.txt'와 'causal_analysis.png'로 저장되었습니다.")
