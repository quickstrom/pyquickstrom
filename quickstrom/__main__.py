from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import executor

# driver = webdriver.Chrome()
# 
# driver.set_network_conditions(
#     offline=False,
#     latency=500,
#     throughput=500*1024,
# )
# 
# driver.get("http://wickstrom.tech")
# assert "Oskar" in driver.title
# driver.close()

executor.Check("next").execute()