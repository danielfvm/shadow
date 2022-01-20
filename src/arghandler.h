#ifndef showArghandlerH
#define showArghandlerH

#include <string.h>

char **argv;
int argc;

void ah_init(int _argc, char **_argv) {
	argv = _argv;
	argc = _argc;
}

/* returns position of argument in argv, or 0 if not exist */
int ah_arg_exist(char *arg) {
	for (int i = 1; i < argc; ++ i) {
		if (strcmp(arg, argv[i]) == 0) {
			return i;
		}
	}
	return 0;
}

/* returns value of argument if set, example: --speed 12 */
char* ah_get_value_of_arg(char *arg) {
	int idx = ah_arg_exist(arg);

	if (idx > 0 && idx + 1 < argc) {
		return argv[idx + 1];
	}
	return NULL;
}

/* multiple argument names for one argument, example: -v --version */
char* ah_get_value_of_args(char *arg1, char *arg2) {
	char *val1 = ah_get_value_of_arg(arg1);
	char *val2 = ah_get_value_of_arg(arg2);

	return val1 == NULL ? val2 : val1;
}

char* ah_or_def(char *val, char *def) {
	return val == NULL ? def : val;
}
#endif
