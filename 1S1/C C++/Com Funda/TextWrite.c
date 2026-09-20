#include <stdio.h>

struct Player
{
    char Name[100];
    int Level;
    int Score;
};

int main()
{
    struct Player player[5];
    int number = 5;

    FILE* fp;
    fp = fopen("C:\\Users\\User\\OneDrive - KMITL\\Desktop\\mytestfile.txt", "w");

    for(int i=0; i<number; i++)
    {
        printf("Player%d Name = ", i+1);
        scanf("%s", player[i].Name);
        printf("Player%d Level = ", i+1);
        scanf("%d", &player[i].Level);
        printf("Player%d Level = ", i+1);
        scanf("%d", &player[i].Score);
    }

    for(int i=0; i<number; i++)
    {
        fprintf(fp, "%s %d %d\n", player[i].Name, player[i].Level, player[i].Score);
    }
    fclose(fp);

    return 0;
}
