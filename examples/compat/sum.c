#include <stdio.h>

int main(void) {
    int values[] = {1, 2, 3, 4};
    int total = 0;
    for (int index = 0; index < 4; index++) {
        total += values[index];
    }
    printf("%d\n", total);
    return 0;
}