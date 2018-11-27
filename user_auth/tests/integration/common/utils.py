def compare_user(test_instance, user_object, expected_hash):
    test_instance.assertEqual(user_object.first_name, expected_hash['first_name'])
    test_instance.assertEqual(user_object.last_name, expected_hash['last_name'])
    test_instance.assertEqual(user_object.email, expected_hash['email'])
    test_instance.assertEqual(user_object.username, expected_hash['email'])


def compare_user_profile(test_instance, user_object, expected_hash):
    test_instance.assertEqual(user_object.contact_no, expected_hash['contact_no'])