import asyncio

from check_libraries import check_nottingham_libraries, check_nottingham_university

check_nottingham_university.main()
asyncio.run(check_nottingham_libraries.main())
