#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function to calculate factorial
int factorial(int n)
{
    if (n <= 1)
    {
        return 1;
    }
    return n * factorial(n - 1);
}

// Function to check if a number is prime
int isPrime(int num)
{
    if (num <= 1)
        return 0;
    if (num <= 3)
        return 1;
    if (num % 2 == 0 || num % 3 == 0)
        return 0;

    for (int i = 5; i * i <= num; i += 6)
    {
        if (num % i == 0 || num % (i + 2) == 0)
        {
            return 0;
        }
    }
    return 1;
}

// Function to reverse a string
void reverseString(char *str)
{
    int len = strlen(str);
    for (int i = 0; i < len / 2; i++)
    {
        char temp = str[i];
        str[i] = str[len - 1 - i];
        str[len - 1 - i] = temp;
    }
}

int main()
{
    printf("Welcome to the C Programming Demo!\n");
    printf("===================================\n\n");

    // Factorial demonstration
    int num = 5;
    printf("1. Factorial of %d: %d\n", num, factorial(num));

    // Prime number check
    int testNum = 17;
    printf("2. Is %d prime? %s\n", testNum, isPrime(testNum) ? "Yes" : "No");

    // String reversal
    char text[] = "Hello World";
    printf("3. Original string: %s\n", text);
    reverseString(text);
    printf("   Reversed string: %s\n", text);

    // Simple loop demonstration
    printf("4. Numbers 1-10: ");
    for (int i = 1; i <= 10; i++)
    {
        printf("%d ", i);
    }
    printf("\n");

    // Array operations
    int numbers[] = {3, 7, 1, 9, 4, 6, 2, 8, 5};
    int size = sizeof(numbers) / sizeof(numbers[0]);
    int sum = 0;

    for (int i = 0; i < size; i++)
    {
        sum += numbers[i];
    }

    printf("5. Array sum: %d\n", sum);
    printf("   Array average: %.2f\n", (float)sum / size);

    printf("\nProgram completed successfully!\n");

    return 0;
}