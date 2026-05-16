#include <iostream>
#include <string>
#include <vector>
#include <map>

using namespace std;

/**
 * Problem: Multiple of 2019
 * Solution: Suffix modulo technique
 * Time complexity: O(N)
 * Space complexity: O(N)
 */

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    string s;
    if (!(cin >> s)) return 0;
    int n = s.length();
    
    // suffix[i] = value of substring s[i..n-1] mod 2019
    vector<int> suffix(n + 1, 0);
    int p10 = 1;
    for (int i = n - 1; i >= 0; i--) {
        int digit = s[i] - '0';
        // s[i..n-1] = s[i] * 10^(n-1-i) + s[i+1..n-1]
        suffix[i] = (digit * p10 + suffix[i + 1]) % 2019;
        p10 = (p10 * 10) % 2019;
    }
    
    // Count pairs (i, j) such that suffix[i] == suffix[j+1]
    // because V(i, j) * 10^(n-1-j) = V(i, n-1) - V(j+1, n-1)
    // and gcd(10, 2019) = 1
    map<int, long long> freq;
    for (int i = 0; i <= n; i++) {
        freq[suffix[i]]++;
    }
    
    long long ans = 0;
    for (auto const& [val, count] : freq) {
        ans += count * (count - 1) / 2;
    }
    
    cout << ans << endl;
    return 0;
}
