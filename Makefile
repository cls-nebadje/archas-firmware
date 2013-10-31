
CRONTAB=archas-firmware-crontab
CROND=/etc/cron.d

install:
	cp ./$(CRONTAB) $(CROND)/

uninstall:
	rm -f $(CROND)/$(CRONTAB)

