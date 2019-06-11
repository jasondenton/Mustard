import os
import jinja2

CURRENT_ENGINE = None

def use_template(obj, template):
	'''example: X | usetemplate('foo')
	Instaniates template foo with objected X'''
	if not CURRENT_ENGINE:
		raise Exception('No template engine registered')
	return CURRENT_ENGINE.Render(obj,template)

def as_set(obj):
	return set(obj)

class TemplateEngine:
	'''Simple helper for jinja2 templates. Looks for templates in X.template.extension" 
	files, where .extension is usually set by the subclass. Impleases the |usetemplate
	filter, allowing for a template to call another template.'''

	def __init__(self, ext, path):
		self.path = path
		self.template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
		self.template_env.filters['usetemplate'] = use_template
		self.template_env.filters['as_set'] = as_set
		self.extension = ext
			
	def Render(self, obj, template):
		global CURRENT_ENGINE
		CURRENT_ENGINE = self
		tname = "%s.template.%s" % (template, self.extension)
		try:
			template = self.template_env.get_template(tname)
		except jinja2.UndefinedError as err:
			raise Exception('Template \"{0}\" not found at path {2}'.format(
				tname, self.extention, self.path))
		except jinja2.TemplateSyntaxError as err:
			line1 = 'Syntax error in on line {0} of template \"{1}\" at path {2}.'.format(
				err.lineno,tname, self.path)
			raise Exception(line1 + '\n\t' + err.message)
		return template.render(obj)
	
class HTMLTemplateEngine (TemplateEngine):
	def __init__(self, path='.'):
		TemplateEngine.__init__(self, 'html', path)
	
	


