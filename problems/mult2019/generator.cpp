#include "testlib.h"
#include <iostream>
#include <string>
#include <vector>

using namespace std;

void gen_random(int n) {
    for (int i = 0; i < n; i++) {
        cout << (char)('1' + rnd.next(0, 8));
    }
    cout << endl;
}

void gen_same(int n) {
    char c = (char)('1' + rnd.next(0, 8));
    for(int i=0; i<n; i++) cout << c;
    cout << endl;
}

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    
    // Polygon passes: generator <seed> <subtask> <n_max>
    // So argv[1] is seed, argv[2] is subtask, argv[3] is n_max
    int subtask = atoi(argv[2]);
    int n_max = atoi(argv[3]);
    
    int n = rnd.next(max(1, n_max / 2), n_max);
    
    if (subtask == 1) {
        gen_same(n);
    } else {
        gen_random(n);
    }
    
    return 0;
}
