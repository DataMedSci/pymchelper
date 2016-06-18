/* Converts pasin.dat to output.inp which can be read by SimpleGeo */
/* Niels Bassler <bassler@phys.au.dk> */
/* Last revision: 13. August 2010 */ 


#include<stdio.h>
#include<stdlib.h>
#include<string.h>

// gcc shield2fluka.c -o shield2fluka -Wall

#define FILENAME_GEOMETRY "pasin.dat"
#define VERSION "1.1"

// getline is a gcc non-standard implementation.
int mygetline(FILE *fp, char s[], int lim);

int main(int argc, char *argv[]) {

	FILE *fp, *fp_out;
	int a,len=100, val[4096],i,n_zones;
	char buff[100], buff2[100];

	if (argc==1) {
		fprintf(stdout, "This is shield2fluka v.%s\n",VERSION);
		fprintf(stdout, "Report bugs to Niels Bassler <bassler@phys.au.dk>.\n\n");
		fprintf(stdout, "Please specify input filename as argument, e.g.:\n\n");
		fprintf(stdout, "  shield2fluka pasin.dat\n");
		exit(0);
	}

	// fp = fopen(FILENAME_GEOMETRY, "r");
	fp = fopen(argv[1], "r");
	if (fp == NULL) {
		fprintf(stderr, "ERROR: could not find file %s\n",argv[1]);
		exit(-1);
	}
	fp_out = fopen("output.inp", "w");
	if (fp_out == NULL) {
		fprintf(stderr, "ERROR: could not open output file\n");
		exit(-1);
	}

	//printf("test\n");

	// build output file
	fprintf(fp_out,"TITLE\n");
	fprintf(fp_out,"SHIELD2FLUKA ver.%s generated .inp file.\n",VERSION);
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	fprintf(fp_out,"DEFAULTS                                                              HADROTHE  \n");
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	fprintf(fp_out,"BEAM           -0.15       0.0       0.0       4.0       4.0       1.0PROTON    \n");
	fprintf(fp_out,"BEAMPOS          0.0       0.0      -1.0       0.0       0.0          POSITIVE  \n");
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	fprintf(fp_out,"GEOBEGIN                                                              COMBINAT  \n");

	/* read and insert regions ; */
	strcpy(buff2,"");

	mygetline(fp, buff, len);
	/* clear first 20 characters of title, is this really neccessray ? */
	for(i=0;i<20;i++)
		buff[i] = ' ';
	fprintf(fp_out,"%s",buff); /* write geometry title header */
	// read fp until and including "END"
	while ( (strcmp(buff2, "END") != 0) ) {
		//    printf("got a card\nC:%s\n",buff);
		mygetline(fp, buff, len);
		sscanf(buff,"%s",buff2);
		fprintf(fp_out,"%s",buff);
	}
	//  fprintf(fp_out,"%s", buff);
	//  printf("test2\n");


	/* insert zone list */
	fprintf(fp_out,"*-reg-----or-----or-----or-----or-----or-----or-----or-----or-----or-----\n");
	strcpy(buff2,""); /* clear buff2 */
	/* read fp until and including "END" */
	while ( strcmp(buff2, "END") != 0 ) {

		mygetline(fp, buff, len);
		sscanf(buff, "%s", buff2);
		/* if buffer is not a continuation card, add a number for memory allocation */
		if (!((buff[2]==' ') && (buff[3]==' ') && (buff[4]==' ')))
			buff[8] = '5';
		fprintf(fp_out,"%s",buff);
	}

	// MISSING: add blackhole card
	fprintf(fp_out,"*-reg-----or-----or-----or-----or-----or-----or-----or-----or-----or-----\n");
	i = 0;
	fprintf(fp_out,"GEOEND\n");
	while (fscanf(fp, "%i", &a) == 1) {
		val[i] = a;
		i++;
	}
	/* val now holds 2 x all zones */
	n_zones = i/2;
	printf("got %i zones  - %i\n", i, n_zones);


	/* insert material assignments */
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	for(i =0; i < n_zones; i++) {
		// last argument +2 because SHIELD vacuum = 0 and FLUKA vacuum = 2
		// dont bother about the other materials
		fprintf(fp_out,"ASSIGNMAT    %5i.0   %5i.0\n", val[i+n_zones] + 2, val[i]);
	}
	// MISSING : add blackhole assignment
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	fprintf(fp_out,"RANDOMIZE        1.0\n");
	fprintf(fp_out,"*---+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8\n");
	fprintf(fp_out,"START         20000.\n");
	fprintf(fp_out,"STOP\n");
	fclose(fp);
	fclose(fp_out);
	return(0);
}

int mygetline(FILE *fp, char s[], int lim) {

	int c, i;

	for (i=0; i<lim-1 && (c=fgetc(fp))!=EOF && c!='\n'; ++i)
		s[i] =c;
	if (c == '\n') {
		s[i]=c;
		++i;
	}
	s[i] = '\0';
	if (c==EOF) {
		return(EOF);
	}
	return i;
}

