#include "testlib.h"
#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    
    int subtask = 1;
    if (argc > 1) {
        subtask = atoi(argv[1]);
    }

    long long a, b;
    if (subtask == 1) {
        a = rnd.next(1, 100);
        b = rnd.next(1, 100);
    } else {
        a = rnd.next(1, 1000000000);
        b = rnd.next(1, 1000000000);
    }

    cout << a << " " << b << endl;
    return 0;
}
