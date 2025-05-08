clc
clear all

A = xlsread('path_to_data.xlsx', 'Sheet1', 'A2:B31'); 
x = A(:, 1);  
data = A(:, 2); 

n = length(data);

v = zeros(n-1, n);
V = zeros(1, n-1);

% Compute V and Ut
for t = 2:n
    for j = 1:n
        v(t-1, j) = sign(data(t-1) - data(j));
    end
    V(t-1) = sum(v(t-1, :));
end

Ut = cumsum(V);  % Cumulative sum
F = Ut';  % Transpose to match dimensions
Kmax = max(abs(F));
chg_point = find(abs(F) == Kmax);  % Find the index of the maximum value

% Compute p-value and critical value
p_value = 2 * exp(-6 * Kmax^2 / (n^3 + n^2));  % Current p-value
p_target = 0.05;  % Target p-value
K_critical = sqrt(-log(p_target / 2) * (n^3 + n^2) / 6);  % Critical value

% Plot
figure(1)
hold on
plot(x(2:end), F, 'k-', 'linewidth', 1.5); % Plot change trend
plot([x(chg_point), x(chg_point)], [-Kmax, Kmax], 'r--', 'linewidth', 1.5); % Vertical line at the change point
plot([x(1), x(n)], [-K_critical, -K_critical], 'b-', 'linewidth', 1.5); % Lower threshold (p=0.05)
plot([x(1), x(n)], [K_critical, K_critical], 'b-', 'linewidth', 1.5);   % Upper threshold (p=0.05)
xlabel('time');
ylabel('MAPI ');
title('Pettitt test for rainfall');
legend('Change trend', 'Change point', 'Threshold (p=0.05)');

% Save plot data and statistical results
plot_data = [x(2:end), F];
result_table = {
    'Maximum absolute value (Kmax)', Kmax;
    'Change point index', chg_point;
    'Change time', x(chg_point);
    'Significance level (current p)', p_value;
    'Upper threshold (p=0.05, +Kcritical)', K_critical;
    'Lower threshold (p=0.05, -Kcritical)', -K_critical;
};

output_filename = 'path_to_output.xlsx'; % Specify the output file path
writecell({'Time', 'Statistic F'}, output_filename, 'Sheet', 'PlotData', 'Range', 'A1');
writematrix(plot_data, output_filename, 'Sheet', 'PlotData', 'Range', 'A2');
writecell(result_table, output_filename, 'Sheet', 'Summary', 'Range', 'A1');

disp(['Plot data and results have been saved to: ', output_filename]);
