#include <stdio.h>

struct Player
{
    char Name[100];
    int Level;
    int Score;
};

int main()
{
    struct Player player;
    int number = 5;

    FILE* fp;
    fp = fopen("C:\\Users\\User\\OneDrive - KMITL\\Desktop\\mytestfile.txt", "rb");

    if (fp == (FILE *)NULL) printf("Cannot open file\n");
    else
        while( fread(&player,sizeof(struct Player),1,fp) == 1 )
    {
            printf("Name: %s\n", player.Name);
            printf("Level: %d and Score: %d\n", player.Level, player.Score);
            printf("---------------------------------\n");
        }

    fclose(fp);

    return 0;
}

