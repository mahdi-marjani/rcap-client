from . import utils

import logging

logging.basicConfig(level=logging.ERROR)

from .browser import Browser
from .detector import Detector

class RecaptchaSolver:

    def __init__(self, browser: Browser, detector: Detector):
        self.browser = browser
        self.detector = detector
        self.last_recaptcha_token = None


    def solve(self):
        self._start()
        self._process()
        self._finish()


    def _start(self):
        self._click_checkbox()


    def _process(self):
        self._solve_challenge()


    def _finish(self):
        self.browser.switch_to_main_frame()


    def _switch_to_challenge_frame(self):
        self.browser.switch_to_frame('//iframe[contains(@title, "challenge") and contains(@title, "recaptcha")]')


    def _click_checkbox(self):
        self.browser.switch_to_frame('//iframe[@title="reCAPTCHA"]')
        self.browser.click('//div[@class="recaptcha-checkbox-border"]', 10)
        self._switch_to_challenge_frame()


    def _solve_challenge(self):
        while True:
            try:
                solved = self._wait_until_challenge_ready_or_solved()
                if solved:
                    break

                captcha_type, target_text, answers, main_image_array = self._analyze_challenge()

                if captcha_type is None:
                    self._reload()
                    continue

                if captcha_type == "dynamic":
                    self._solve_dynamic(target_text, answers, main_image_array)
                else:
                    self._click_answers(answers)

                if self._verify():
                    break

            except Exception as e:
                logging.exception("An error occurred")
                self._recover_from_error()


    def _wait_until_challenge_ready_or_solved(self):
        for _ in range(200):
            try:
                self._switch_to_challenge_frame()
                self.browser.wait_for(
                    '//button[@id="recaptcha-verify-button" and not(contains(@class, "rc-button-default-disabled"))]',
                    0.1,
                    'present'
                )
                return False
            except Exception:
                if self._is_checkbox_checked():
                    return True

        return False


    def _is_checkbox_checked(self):
        self.browser.switch_to_frame('//iframe[@title="reCAPTCHA"]')
        recaptcha_anchor = self.browser.find_element('//span[@id="recaptcha-anchor"]', 10, 'present')
        return self.browser.get_attribute(recaptcha_anchor, 'aria-checked') == 'true'


    def _analyze_challenge(self):
        self._switch_to_challenge_frame()

        recaptcha_token_input = self.browser.find_element(
            f'//input[@id="recaptcha-token" and not(@value="{self.last_recaptcha_token}")]',
            10,
            'present'
        )

        self.last_recaptcha_token = self.browser.get_attribute(recaptcha_token_input, 'value')

        title_wrapper = self.browser.find_element('//*[@id="rc-imageselect"]', 10, 'present')

        target = self.browser.find_element_inside_element(title_wrapper, './/strong')
        target_text = self.browser.get_element_text(target)

        if not self.detector.is_model_available(target_text):
            return None, None, None, None

        title_wrapper_text = self.browser.get_element_text(title_wrapper)
        
        if "squares" in title_wrapper_text:
            return self._handle_4x4(target_text)

        if "none" in title_wrapper_text:
            return self._handle_dynamic_3x3(target_text)

        return self._handle_static_3x3(target_text)


    def _handle_4x4(self, target_text):
        img_urls = self._get_captcha_image_urls()
        main_image_array = utils.get_image_array(img_urls[0])

        answers = self.detector.detect(main_image_array, "4x4", target_text)
        if 1 <= len(answers) < 16:
            return "squares", target_text, answers, main_image_array

        return None, None, None, None


    def _get_captcha_image_urls(self):
        images = self.browser.find_elements('//div[@id="rc-imageselect-target"]//img', 10, 'present')
        
        return [self.browser.get_attribute(img, 'src') for img in images]


    def _handle_dynamic_3x3(self, target_text):
        img_urls = self._get_captcha_image_urls()
        if len(set(img_urls)) != 1:
            return None, None, None, None

        main_image_array = utils.get_image_array(img_urls[0])
        answers = self.detector.detect(main_image_array, "3x3", target_text)

        if len(answers) > 2:
            return "dynamic", target_text, answers, main_image_array

        return None, None, None, None


    def _handle_static_3x3(self, target_text):
        img_urls = self._get_captcha_image_urls()
        main_image_array = utils.get_image_array(img_urls[0])

        answers = self.detector.detect(main_image_array, "3x3", target_text)
        if len(answers) > 2:
            return "selection", target_text, answers, main_image_array

        return None, None, None, None


    def _reload(self):
        self._switch_to_challenge_frame()
        self.browser.click('//*[@id="recaptcha-reload-button"]', 10)


    def _solve_dynamic(self, target_text, answers, main_image_array):
        self._click_answers(answers)

        while True:
            old_urls = self._get_captcha_image_urls()
            is_new, new_urls = self._wait_for_new_dynamic_images(
                answers, old_urls
            )

            new_images_array = self._download_dynamic_images(answers, new_urls)
            main_image_array = self._merge_dynamic_images(answers, main_image_array, new_images_array)

            answers = self.detector.detect(main_image_array, "3x3", target_text)
            if not answers:
                break

            self._click_answers(answers)


    def _click_answers(self, answers):
        for answer in answers:
            self.browser.click(f'(//div[@id="rc-imageselect-target"]//td)[{answer}]', 10)


    def _wait_for_new_dynamic_images(self, answers, old_urls):
        while True:
            is_new, new_urls = self._get_new_dynamic_image_urls(
                answers, old_urls
            )
            if is_new:
                return is_new, new_urls


    def _get_new_dynamic_image_urls(self, answers, old_urls):
        images = self.browser.find_elements('//div[@id="rc-imageselect-target"]//img', 10, 'present')
        new_urls = []

        for img in images:
            try:
                new_urls.append(self.browser.get_attribute(img, 'src'))
            except:
                is_new = False
                return is_new, new_urls

        same_count = 0
        for answer in answers:
            if new_urls[answer - 1] == old_urls[answer - 1]:
                same_count += 1

        if same_count > 0:
            is_new = False
            return is_new, new_urls
        else:
            is_new = True
            return is_new, new_urls


    def _download_dynamic_images(self, answers, img_urls):
        new_images_array = {}
        for answer in answers:
            idx = answer - 1
            new_images_array[answer] = utils.get_image_array(img_urls[idx])
        
        return new_images_array


    def _merge_dynamic_images(self, answers, main_image_array, new_images_array):
        while True:
            try:
                for answer in answers:
                    new_image_array = new_images_array[answer]
                    main_image_array = utils.paste_image_on_main(main_image_array, new_image_array, answer)
                return main_image_array
            except Exception:
                continue


    def _verify(self):
        self.browser.click('//*[@id="recaptcha-verify-button"]', 10)

        return self._wait_until_challenge_ready_or_solved()


    def _recover_from_error(self):
        try:
            self._click_checkbox()
        except Exception:
            pass
