import pandas as pd
import numpy as np
import concurrent.futures
import json

def hayashi_yoshida_estimator(df1, df2):
    # df1, df2 must have time(timestamp) and return columns 
    temp_df1 = df1.iloc[1:]['return']
    temp_df2 = df2.iloc[1:]['return']
    
    # Make interval
    I1 = pd.IntervalIndex.from_arrays(df1.index[:-1], df1.index[1:])
    I2 = pd.IntervalIndex.from_arrays(df2.index[:-1], df2.index[1:])

    # Calculate covariances
    hy_cov = 0
    minarg = 0
    for i2 in I2:
        # for each interval of df2
        
        found = False
        for i in range(minarg, len(I1)):
            # for each interval from previous interval's end
            
            if (I1[i].left < i2.right) and (I1[i].right > i2.left):
                # if overlap two intervals.
                # calculate covariance
                hy_cov += temp_df1.loc[I1[i].right] * temp_df2.loc[i2.right]
                
                # set params for next iter.
                found = True
                minarg = i

            elif I1[i].left > i2.right:
                # overlap is not init. (at the Begining)
                break
            elif I1[len(I1) - 1].right <= i2.left:
                # overlap is not init (at the End)
                break
            elif found:
                # if overlap series is ended.
                break
        
    # calculate HY estimator    
    hy_corr = hy_cov / np.sqrt(np.sum(temp_df1 ** 2) * np.sum(temp_df2 ** 2))
    return hy_corr

def generate_poisson_timestamps(lambda_, T, dt):
    """Generate Poisson timestamps."""
    n = int(T / dt)
    p_event = lambda_ * dt  # Probability of an event in each step
    time_steps = np.arange(0, T, dt)
    events = np.random.rand(len(time_steps)) < p_event
    return time_steps[events]

def simulate_correlated_brownian_motion(T, dt, rho):
    """Simulate two correlated Brownian motions."""
    n = int(T / dt)
    time_grid = np.linspace(0, T, n)
    B1 = np.random.normal(0, np.sqrt(dt), size=n).cumsum()
    W = np.random.normal(0, np.sqrt(dt), size=n).cumsum()
    B2 = rho * B1 + np.sqrt(1 - rho**2) * W
    return time_grid, B1, B2

def sample_brownian_at_poisson(B, timestamps, time_grid):
    """Sample Brownian motion at given Poisson timestamps."""
    return np.interp(timestamps, time_grid, B)

def get_simulated_corr(T, dt, lambda1, lambda2, rho, lag):
    # Generate Poisson timestamps
    timestamps1 = generate_poisson_timestamps(lambda1, T, dt)
    timestamps2 = generate_poisson_timestamps(lambda2, T, dt)

    # Simulate correlated Brownian motions
    time_grid, B1, B2 = simulate_correlated_brownian_motion(T, dt, rho)

    # Sample Brownian motions at Poisson timestamps
    X = sample_brownian_at_poisson(B1, timestamps1, time_grid)
    Y = sample_brownian_at_poisson(B2, timestamps2, time_grid)

    df1 = pd.DataFrame({"time":np.arange(0, T, dt)})
    df1_sub = pd.DataFrame({"time": timestamps1, "price":X})
    df1_sub['return'] = df1_sub['price'].diff()
    df1_sub['time'] = df1_sub['time'] + int(lag)
    df1 = pd.merge_asof(df1, df1_sub, 'time')
    

    df2 = pd.DataFrame({"time":np.arange(0, T, dt)})
    df2_sub = pd.DataFrame({"time": timestamps2, "price":Y})
    df2_sub['return'] = df2_sub['price'].diff()
    df2 = df2.merge(df2_sub, how='left', on='time')
    
    last_tick = df2.ffill()['return'].corr(df1.ffill()['return'])
    hy = hayashi_yoshida_estimator(df1_sub, df2_sub)
    return [last_tick, hy]

# 병렬로 실행할 작업 함수
def run_simulation(T, dt, lambda1, lambda2, rho, lag, n_trial):
    corr_list = []
    for _ in range(n_trial):
        corr_list.append(get_simulated_corr(T, dt, lambda1, lambda2, rho, lag))
    corr_mean = np.mean(corr_list, axis=0)
    return [lag, corr_mean[0], corr_mean[1]]

if __name__ == "__main__":
    # Parameters
    T = 30600  # Total time
    dt = 5     # Time step
    lambda1 = 0.1  # Intensity for process 1
    lambda2_grid = [0.1 / i for i in [1, 2, 4, 6, 8, 10, 20]]  # Intensity for process 2
    rho = 0.8  # Correlation between the Brownian motions
    n_trial = 10  # Number of trials
    lag_grid = list(range(-100, 110, 10))  # Lag grid

    # 병렬 처리로 실행
    corr_dict = {}

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for lambda2 in lambda2_grid:
            lambda_ratio = str(lambda1 / lambda2)
            lagcorr_list = []
            print(f"Processing: {lambda_ratio}")
            # 각 lag에 대한 작업 병렬 실행
            future_to_lag = {
                executor.submit(run_simulation, T, dt, lambda1, lambda2, rho, lag, n_trial): lag
                for lag in lag_grid
            }
            print(f"Each Lag completed of {lambda_ratio}")

            for future in concurrent.futures.as_completed(future_to_lag):
                result = future.result()  # [lag, corr_mean_0, corr_mean_1]
                lagcorr_list.append(result)

            # 결과 정렬 (lag 순서대로)
            lagcorr_list.sort(key=lambda x: x[0])
            corr_dict[lambda_ratio] = lagcorr_list

    # 결과를 JSON 파일로 저장
    output_file = "simulation_results.json"
    with open(output_file, "w") as f:
        json.dump(corr_dict, f, indent=4)

    print(f"결과가 {output_file}에 저장되었습니다.")
