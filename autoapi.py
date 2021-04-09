from webbot import Browser
import time

class Automate():
    def __init__(self, showWindow = False, proxy = None):
        self.proxy = proxy
        self.web = Browser(showWindow=showWindow, proxy=proxy)

    def enter_number(self, number):
        try:
            self.web.go_to('https://my.telegram.org/auth?to=activate')
            self.web.type(number, id="my_login_phone")
            self.web.click("Next")
            time.sleep(6)
            return True
        except Exception:
            return False

    def enter_code(self, code):
        try:
            self.web.type(code, id="my_password")
            self.web.click("Sign In")
            time.sleep(3)
            self.web.click("API development tools")
            time.sleep(3)
            return True
        except Exception:
            return False
    
    def make_application(self):
        self.web.type("SMS App", id="app_title")
        self.web.type("smsapp", id="app_shortname")
        # click the fucking radio thingie, otherwise gives an error?
        self.web.click(xpath="//*[@id=\"app_create_form\"]/div[4]/div/div[8]/label/input")
        self.web.type("sms app script", id="app_desc")
        self.web.click("Create application")
        time.sleep(3)
        return True

    def get_api(self):
        api_id = self.web.find_elements(tag="strong", xpath="//*[@id=\"app_edit_form\"]/div[1]/div[1]/span/strong")[0].text
        api_hash = self.web.find_elements(tag="strong", xpath="//*[@id=\"app_edit_form\"]/div[2]/div[1]/span")[0].text
        return {"api_id": int(api_id), "api_hash": api_hash}
