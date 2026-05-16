#include <iostream>
#include <string>

using namespace std;

/**
 * Wrong Answer solution: Always returns a wrong value
 */

int main() {
    string s;
    if (!(cin >> s)) return 0;
    // Always return a value that is unlikely to be correct
    cout << -1 << endl;
    return 0;
}
