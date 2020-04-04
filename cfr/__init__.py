from pathlib import Path

__all__ = ("javaCompile",)
import typing
from pathlib import Path
from JAbs import SelectedJVMInitializer

cfrReaderNs = "org.benf.cfr.reader"
cfrReaderUtilNs = cfrReaderNs + ".util"

neededCFRClasses = [
	"java.util.HashMap",
	"java.util.List",
	"java.lang.StringBuilder",
	cfrReaderNs + ".Main",
	cfrReaderNs + ".PluginRunner",
	cfrReaderNs + ".mapping.MappingFactory",
	cfrReaderNs + ".mapping.ObfuscationMapping",
	cfrReaderNs + ".relationship.MemberNameResolver",
	cfrReaderNs + ".state.ClassFileSourceImpl",
	cfrReaderNs + ".state.TypeUsageCollectingDumper",
	cfrReaderNs + ".Driver",
	cfrReaderNs + ".api.CfrDriver",
	cfrReaderNs + ".CfrDriverImpl",
	cfrReaderNs + ".api.OutputSinkFactory",
	cfrReaderNs + ".bytecode.analysis.parse.utils.Pair",
	cfrReaderNs + ".state.DCCommonState",
	cfrReaderUtilNs + ".AnalysisType",
	cfrReaderUtilNs + ".getopt.GetOptParser",
	cfrReaderUtilNs + ".getopt.Options",
	cfrReaderUtilNs + ".getopt.OptionsImpl",
	cfrReaderUtilNs + ".output.DumperFactory",
	cfrReaderUtilNs + ".output.StringStreamDumper",
	cfrReaderUtilNs + ".output.IllegalIdentifierDump",
]


def getCFRPath() -> Path:
	return Path("./cfr-0.149.jar")


CFRClassPath = getCFRPath()
ji = SelectedJVMInitializer([CFRClassPath], neededCFRClasses)


class EntityDecompilator:
	__slots__ = ("entity", "parent")

	def __init__(self, parent: typng.Union[Decompilation, "EntityDecompilator"]) -> None:
		self.parent = parent

	def decompile(self, entity=None):
		if entity is None:
			entity = self.entity

		return self.parent.decompile(entity)


class MethodDecompilation(EntityDecompilator):
	def __init__(self, parent: ClassDecompilation, name: str, signature=None) -> None:
		super().__init__(parent)
		# ji.MemberNameResolver.resolveNames(s);
		ms = parent.entity.getMethodByName(name)
		self.entity = list(ms)[0]  # TODO: implement signature matching

		# private, needs fixes in CFR
		# self.lineNumberTable = dict(self.entity.codeAttribute.lineNumberTable.entries)

	def decompile(self, entity=None) -> str:
		if entity is None:
			entity = self.entity
			# private, needs fixes in CFR
			# maps instruction numbers to statements and blocks. Don't map bytes. But the lineNumberTable seems to be mapping bytes to lines. Need a way to map statements to bytes
			#for bs in self.entity.analysis.statement.blockStatements:
			#	if(hasattr(bs, "instrIndex")):
			#		print(bs, "// " + str(bs.instrIndex.index)) #
			#	else:
			#		print(bs)

		return self.parent.decompile(entity)


class ClassDecompilation(EntityDecompilator):
	__slots__ = ("typeUsageInformation", "collectingDumper", "parent")

	def __init__(self, parent: Decompilation, classToDecompile: str) -> None:
		super().__init__(parent)
		self.entity = parent.state.getClassFileMaybePath(classToDecompile)
		parent.state.configureWith(self.entity)
		self.entity.loadInnerClasses(parent.state)
		self.collectingDumper = ji.TypeUsageCollectingDumper(parent.opts, self.entity)
		self.entity.analyseTop(parent.state, self.collectingDumper)
		self.typeUsageInformation = self.collectingDumper.getRealTypeUsageInformation()
		#ji.MemberNameResolver.resolveNames(parent.state);

	def analyseMethod(self, name: str) -> MethodDecompilation:
		return MethodDecompilation(self, name)

	def decompile(self, entity=None):
		if entity is None:
			entity = self.entity

		return self.parent.decompile(entity, typeUsageInformation=self.typeUsageInformation)


class Decompilation:
	__slots__ = ("cfs", "state", "illegalIdentifierDump", "mapping", "opts")

	def __init__(self, opts=None) -> None:
		if opts is None:
			opts = {}
		self.opts = ji.OptionsImpl(ji.HashMap(opts))
		self.cfs = ji.ClassFileSourceImpl(self.opts)
		self.state = ji.DCCommonState(self.opts, self.cfs)
		self.illegalIdentifierDump = ji.IllegalIdentifierDump.Factory.get(self.opts)
		self.mapping = None

	def appendClassPath(self, jarPath: Path) -> None:
		self.state.explicitlyLoadJar(str(jarPath), ji.AnalysisType.JAR)
		self.mapping = ji.MappingFactory.get(self.opts, self.state)

	def loadClass(self, classToDecompile: str) -> ClassDecompilation:
		return ClassDecompilation(self, classToDecompile)

	def decompile(self, entity, typeUsageInformation=None):
		b = ji.StringBuilder()
		d = ji.StringStreamDumper(None, b, typeUsageInformation, self.opts, self.illegalIdentifierDump)
		entity.dump(d, False)
		d.close()
		res = str(b.toString())
		return res
