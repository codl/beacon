import util
import doctest

fail, test = doctest.testmod(util)
print("%s out %s tests successful" % (test - fail, test))

exit(fail)
