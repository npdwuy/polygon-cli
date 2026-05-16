#include <iostream>
#include <string>

using namespace std;

/**
 * Brute force solution for Subtask 2 (|S| <= 2000)
 * Time complexity: O(N^2)
 */

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    string s;
    if (!(cin >> s)) return 0;
    int n = s.length();
    long long ans = 0;
    for (int i = 0; i < n; i++) {
        int current = 0;
        for (int j = i; j < n; j++) {
            current = (current * 10 + (s[j] - '0')) % 2019;
            if (current == 0) ans++;
        }
    }
    cout << ans << endl;
    return 0;
}
